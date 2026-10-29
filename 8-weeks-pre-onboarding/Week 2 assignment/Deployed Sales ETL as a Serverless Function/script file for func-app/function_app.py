import azure.functions as func
import logging
import json
import os
import io

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import pandas as pd


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def read_parquet_from_blob(folder_path):

    account_name = os.environ["STORAGE_ACCOUNT_NAME"]

    account_url = f"https://{account_name}.blob.core.windows.net"

    credential = DefaultAzureCredential()

    blob_service_client = BlobServiceClient(
        account_url=account_url,
        credential=credential
    )

    container_client = blob_service_client.get_container_client(
        "retail-kpi"
    )

    # Find a Parquet file inside the specified folder
    blobs = container_client.list_blobs(
        name_starts_with=folder_path + "/"
    )

    parquet_blob = None

    for blob in blobs:
        if blob.name.lower().endswith(".parquet"):
            parquet_blob = blob.name
            break

    if parquet_blob is None:
        raise FileNotFoundError(
            f"No Parquet file found in {folder_path}"
        )

    logging.info(f"Reading blob: {parquet_blob}")

    blob_client = container_client.get_blob_client(
        parquet_blob
    )

    data = blob_client.download_blob().readall()

    return pd.read_parquet(io.BytesIO(data))


@app.route(route="sales_kpi", methods=["GET"])
def sales_kpi(req: func.HttpRequest) -> func.HttpResponse:

    logging.info("Sales KPI API request received.")

    try:

        # Read KPI summary
        kpi_df = read_parquet_from_blob(
            "kpi_summary"
        )

        # Read regional sales
        region_df = read_parquet_from_blob(
            "regional_sales"
        )

        # Extract KPI row
        kpi = kpi_df.iloc[0]

        # Find top region
        top_region = (
            region_df
            .sort_values(
                "total_sales",
                ascending=False
            )
            .iloc[0]["region"]
        )

        result = {
            "total_orders": int(kpi["total_orders"]),
            "total_units_sold": int(kpi["total_units_sold"]),
            "total_revenue": float(kpi["total_revenue"]),
            "average_order_value": float(
                kpi["average_order_value"]
            ),
            "average_selling_price": float(
                kpi["average_selling_price"]
            ),
            "cancellation_rate": float(
                kpi["cancellation_rate"]
            ),
            "top_region": str(top_region)
        }

        logging.info(
            f"Sales KPI calculation completed. "
            f"Total revenue: {result['total_revenue']}, "
            f"Top region: {result['top_region']}"
        )

        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:

        logging.exception(
            "Sales KPI API failed."
        )

        return func.HttpResponse(
            json.dumps({
                "error": "Unable to calculate sales KPIs",
                "details": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )


@app.timer_trigger(
    schedule="0 0 0 * * 0",
    arg_name="timer",
    run_on_startup=False
)
def scheduled_kpi(timer: func.TimerRequest) -> None:

    logging.info("Weekly KPI calculation started.")

    try:
        kpi_df = read_parquet_from_blob(
            "kpi_summary"
        )

        region_df = read_parquet_from_blob(
            "regional_sales"
        )

        kpi = kpi_df.iloc[0]

        top_region = (
            region_df
            .sort_values(
                "total_sales",
                ascending=False
            )
            .iloc[0]["region"]
        )

        logging.info(
            f"Weekly KPI completed. "
            f"Revenue: {kpi['total_revenue']}, "
            f"Orders: {kpi['total_orders']}, "
            f"Top Region: {top_region}"
        )

    except Exception:
        logging.exception(
            "Weekly KPI calculation failed."
        )