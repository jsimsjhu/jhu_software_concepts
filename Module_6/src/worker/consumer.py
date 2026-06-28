"""RabbitMQ consumer for GradCafe tasks."""

import os
import json
import time
from datetime import datetime
import pika
import psycopg
from scrape import scrape_gradcafe  # You'll need to implement this function

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://app_user:app_password@db:5432/postgres")

EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"


def _open_channel():
    """Open RabbitMQ channel and declare durable entities."""
    params = pika.URLParameters(RABBITMQ_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    return conn, ch


def get_watermark(conn, source="gradcafe"):
    """Get the last_seen value from watermark table."""
    with conn.cursor() as cur:
        cur.execute("SELECT last_seen FROM ingestion_watermarks WHERE source = %s;", (source,))
        result = cur.fetchone()
        return result[0] if result else None


def update_watermark(conn, source, last_seen):
    """Update the watermark with the latest value."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO ingestion_watermarks (source, last_seen, updated_at)
            VALUES (%s, %s, now())
            ON CONFLICT (source) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = now();
        """, (source, last_seen))
        conn.commit()


def handle_scrape_new_data(conn, payload):
    """Scrape new data since the last watermark."""
    print(f"Handling scrape_new_data with payload: {payload}")
    
    source = payload.get("source", "gradcafe")
    since = payload.get("since")
    
    # Get watermark if no since provided
    if not since:
        with conn.cursor() as cur:
            cur.execute("SELECT last_seen FROM ingestion_watermarks WHERE source = %s;", (source,))
            result = cur.fetchone()
            since = result[0] if result else None
    
    print(f"Scraping data since: {since}")
    
    try:
        # Call the actual scraper
        from scrape import scrape_gradcafe
        results = scrape_gradcafe(
            search_query="computer science",
            max_pages=2,
            headless=True
        )
        
        inserted = 0
        if results:
            with conn.cursor() as cur:
                for entry in results:
                    cur.execute("""
                        INSERT INTO applicants (
                            program, comments, date_added, url, status, term,
                            us_or_international, gpa, gre, gre_v, gre_aw, degree,
                            llm_generated_program, llm_generated_university
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                    """, (
                        entry.get("program"),
                        entry.get("comments"),
                        entry.get("added_on"),
                        entry.get("result_url"),
                        entry.get("acceptance_status"),
                        entry.get("term"),
                        entry.get("applicant_type"),
                        entry.get("gpa"),
                        entry.get("gre_quant"),
                        entry.get("gre_verbal"),
                        entry.get("gre_aw"),
                        entry.get("degree"),
                        entry.get("llm_generated_program"),
                        entry.get("llm_generated_university"),
                    ))
                    inserted += 1
                
                # Update watermark with latest date
                if inserted > 0:
                    latest_date = max(r.get("added_on") for r in results if r.get("added_on"))
                    cur.execute("""
                        INSERT INTO ingestion_watermarks (source, last_seen, updated_at)
                        VALUES (%s, %s, now())
                        ON CONFLICT (source) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = now();
                    """, (source, latest_date))
        
        conn.commit()
        print(f"Inserted {inserted} new records")
        return True
        
    except Exception as e:
        print(f"Scrape error: {e}")
        conn.rollback()
        return False


def handle_recompute_analytics(conn, payload):
    """Recompute analytics summaries."""
    print(f"Handling recompute_analytics with payload: {payload}")

    # Refresh materialized view or recompute summary
    with conn.cursor() as cur:
        # Example: Create or refresh a summary table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analytics_summary (
                metric_name TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMPTZ DEFAULT now()
            );
        """)
        conn.commit()

    print("Analytics recomputed")
    return True


def callback(ch, method, properties, body):
    """Process incoming RabbitMQ messages."""
    try:
        data = json.loads(body.decode("utf-8"))
        kind = data.get("kind")
        payload = data.get("payload", {})
        print(f"Received task: {kind} at {datetime.now().isoformat()}")

        with psycopg.connect(DATABASE_URL) as conn:
            if kind == "scrape_new_data":
                success = handle_scrape_new_data(conn, payload)
            elif kind == "recompute_analytics":
                success = handle_recompute_analytics(conn, payload)
            else:
                print(f"Unknown task kind: {kind}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            if success:
                conn.commit()
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                conn.rollback()
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except psycopg.Error as e:
        print(f"Database error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    """Start the worker consumer."""
    print("Worker starting...", flush=True)
    conn, ch = _open_channel()
    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=QUEUE, on_message_callback=callback, auto_ack=False)
    print("Worker is running. Waiting for messages...", flush=True)
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        print("Worker stopped.", flush=True)
        conn.close()


if __name__ == "__main__":
    main()
