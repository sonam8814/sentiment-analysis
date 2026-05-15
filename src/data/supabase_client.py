"""Supabase connection and query layer for NPS responses."""

from datetime import date

import pandas as pd
import streamlit as st
from loguru import logger
from supabase import Client, create_client

from config.settings import get_settings
from src.utils.exceptions import SupabaseConnectionError

_PAGE_SIZE = 1000


@st.cache_resource
def get_supabase_client() -> Client:
    """Return a cached Supabase client instance.

    Returns:
        A configured Supabase Client.

    Raises:
        SupabaseConnectionError: If client creation fails.
    """
    settings = get_settings()
    try:
        client = create_client(settings.supabase_url, settings.supabase_anon_key)
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as exc:
        logger.error(f"Failed to create Supabase client: {exc}")
        raise SupabaseConnectionError(f"Could not connect to Supabase: {exc}") from exc


def fetch_responses(
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 10000,
) -> pd.DataFrame:
    """Fetch NPS responses from Supabase with optional date filtering and pagination.

    Args:
        start_date: Include responses on or after this date.
        end_date: Include responses on or before this date.
        limit: Maximum total rows to return.

    Returns:
        DataFrame with raw NPS response data.

    Raises:
        SupabaseConnectionError: If the query fails.
    """
    client = get_supabase_client()
    settings = get_settings()
    table_name = settings.supabase_table_name

    try:
        all_rows: list[dict] = []
        offset = 0

        while offset < limit:
            page_size = min(_PAGE_SIZE, limit - offset)
            query = client.table(table_name).select("*")

            if start_date is not None:
                query = query.gte("response_date", start_date.isoformat())
            if end_date is not None:
                query = query.lte("response_date", end_date.isoformat())

            query = query.order("response_date", desc=True)
            query = query.range(offset, offset + page_size - 1)

            response = query.execute()
            rows = response.data

            if not rows:
                break

            all_rows.extend(rows)
            logger.debug(f"Fetched page: offset={offset}, rows={len(rows)}")

            if len(rows) < page_size:
                break

            offset += page_size

        logger.info(f"Total rows fetched from Supabase: {len(all_rows)}")

        if not all_rows:
            return pd.DataFrame(
                columns=[
                    "id",
                    "created_at",
                    "response_date",
                    "nps_score",
                    "comment",
                    "customer_id",
                    "segment",
                ]
            )

        df = pd.DataFrame(all_rows)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["response_date"] = pd.to_datetime(df["response_date"]).dt.date

        return df

    except SupabaseConnectionError:
        raise
    except Exception as exc:
        logger.error(f"Supabase query failed: {exc}")
        raise SupabaseConnectionError(f"Failed to fetch responses: {exc}") from exc
