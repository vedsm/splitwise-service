from fastapi import APIRouter
from pydantic import BaseModel

from src.models.user_models import User

user_router = APIRouter()


@user_router.post("/user")
def create_user(user: User):
    created_user_id = user.save()
    print("New user successfully created with id", created_user_id)
    return {"status": "ok", "user_id": created_user_id, "user": user}


# import os
# import json
# import time
# import pandas as pd
# import pymongo
# import traceback

# from collections import defaultdict
# from datetime import date, datetime, timedelta, timezone
# from dateutil import parser, tz
# from pymongo import UpdateOne, InsertOne
# from fastapi import APIRouter, Depends, BackgroundTasks
# from fastapi import FastAPI, HTTPException, Request, Header
# from fastapi.exceptions import RequestValidationError
# from starlette.responses import Response, JSONResponse

# from jio.health.toolkit.events.iot.DeviceEvent import (
#     DeviceEvent,
#     LastSyncRequest,
#     HealthDevice,
#     DropData,
#     FetchAggregatedData,
#     FetchRawData,
#     FetchLatestData,
#     HealthDevicePreference,
# )

# # from ..models.DeviceEvent import (
# #     DropData,
# #     FetchAggregatedData,
# #     FetchRawData,
# #     FetchLatestData,
# #     HealthDevicePreference,
# # )
# from ..enums.config_enums import Aggregators
# from ...utils.log_util import logger
# from ..processors.aggregation_utils import (
#     get_aggregated_device_data_query,
#     restructure_data_points_individual_devices,
#     restructure_data_points_combined_devices,
#     get_raw_device_data_query,
#     get_latest_device_data_point_query,
#     aggregate_datetime_grouped_data,
# )
# from ..processors.index_model import (
#     user_device_starttime_index,
#     user_device_last_index,
# )
# from ..processors.helpers import (
#     add_user_for_digital_twin_sync,
#     get_iso_datetime_in_ist,
#     check_device_link_status,
#     get_count_of_actively_linked_devices,
#     unlink_oldest_active_device,
# )
# from ..settings import (
#     IST_TIMEZONE,
#     NO_DEVICE_REG_CHANNELS,
#     MAX_LINKED_DEVICE_LIMIT,
#     DATA_DELETION_ALLOWED_CHANNELS,
#     DATETIME_STRING_FORMAT,
#     DAY_SECONDS,
#     MAX_DAYS,
#     MAX_NUMBER_OF_BUCKETS,
#     MIN_BUCKET_SECONDS,
# )
# from ..processors.api_utils import log_backdated_request
# from ..processors.chronos_startup_utils import app_configurations
# from ..processors.digital_twin_utils import (
#     ditto_get_entity_by_data_source,
#     ditto_get_entities,
# )
# from ..auth import verify_client
# from ..db_config import (
#     CHRONOS_DIGITAL_TWIN_SYNC_COLLECTION,
#     USER_DEVICE_MAPPINGS_COLLECTION,
#     collections_as_map,
#     myclient,
# )


# mydb = myclient.get_default_database()
# CHRONOS_COLLECTIONS = collections_as_map(mydb)


# chronos_router = APIRouter()


# @chronos_router.post("/api/metric/add", dependencies=[Depends(verify_client)])
# async def post_metric_event(
#     body_data: DeviceEvent,
#     background_tasks: BackgroundTasks,
#     user_id: str = Header(...),
# ):

#     jhh_user_id = user_id
#     data_dict = body_data.dict()
#     health_device_id = data_dict.get("health_device_id")
#     channel_type = data_dict.get("channel_type", "JHH_APP")

#     if channel_type not in NO_DEVICE_REG_CHANNELS:
#         is_device_linked = check_device_link_status(
#             mydb, USER_DEVICE_MAPPINGS_COLLECTION, user_id, health_device_id
#         )

#         if not is_device_linked:
#             return JSONResponse(
#                 status_code=400,
#                 content="Cannot add data, device not linked with user.",
#             )

#     metric_id = data_dict.get("metric_id")
#     metric_mappings = app_configurations.get_app_config()
#     if metric_id not in metric_mappings:
#         logger.warning("Unrecognized metric_id - {}".format(metric_id))
#         return JSONResponse(status_code=422, content="Unrecognized metric_id")

#     entity_dict = app_configurations.get_app_config().get(metric_id)
#     collection_name = entity_dict.get("core_entity").get("underscored_name")
#     if collection_name not in CHRONOS_COLLECTIONS:
#         mydb[collection_name].create_indexes(
#             indexes=[user_device_starttime_index, user_device_last_index]
#         )
#         CHRONOS_COLLECTIONS[collection_name] = True
#         logger.debug("Index created for {}".format(collection_name))

#     metric_sample_list = data_dict.get("samples", [])
#     if len(metric_sample_list) == 0:
#         return JSONResponse(status_code=422, content="samples list empty")

#     query_list = []
#     for sample in metric_sample_list:
#         if sample == {}:
#             continue
#         start_time = sample.get("start_time")
#         start_time_ist = get_iso_datetime_in_ist(start_time)
#         if not start_time_ist:
#             return JSONResponse(
#                 status_code=400,
#                 content="Invalid isoformat string - {}".format(start_time),
#             )

#         sample["start_time"] = parser.parse(start_time_ist)
#         day = start_time_ist.split("T")[0].replace("-", "")
#         day = int(day)

#         if not sample.get("end_time"):
#             end_time_ist = start_time_ist
#             sample["end_time"] = parser.parse(end_time_ist)
#         else:
#             end_time = sample.get("end_time")
#             end_time_ist = get_iso_datetime_in_ist(end_time)
#             sample["end_time"] = parser.parse(end_time_ist)

#         query = UpdateOne(
#             {
#                 "user_id": jhh_user_id,
#                 "channel_type": channel_type,
#                 "health_device_id": health_device_id,
#                 "nsamples": {"$lt": 5},
#                 "day": day,
#             },
#             {
#                 "$push": {"samples": sample},
#                 "$min": {
#                     "first": parser.parse(start_time_ist),
#                     "document_created_at": datetime.utcnow(),
#                 },
#                 "$max": {"last": parser.parse(end_time_ist)},
#                 "$inc": {"nsamples": 1},
#             },
#             True,
#         )

#         query_list.append(query)
#     mycollection = mydb[collection_name]

#     try:
#         query_result = mycollection.bulk_write(query_list)
#         assert (
#             add_user_for_digital_twin_sync(
#                 mydb,
#                 user_id,
#                 collection_name,
#                 CHRONOS_DIGITAL_TWIN_SYNC_COLLECTION,
#             )
#             == True
#         )
#         background_tasks.add_task(
#             log_backdated_request, user_id, entity_dict, body_data
#         )
#         return JSONResponse(
#             status_code=200, content=str(query_result.bulk_api_result)
#         )
#     except Exception as exc:
#         traceback.print_tb(exc.__traceback__)
#         return JSONResponse(
#             status_code=500, content="Database error - {}".format(str(exc))
#         )


# @chronos_router.post(
#     "/api/metric/last-sync", dependencies=[Depends(verify_client)]
# )
# async def get_user_metric_last_sync(
#     body_data: LastSyncRequest, user_id: str = Header(...)
# ):

#     metric_id_list = body_data.metric_id
#     health_device_id = body_data.health_device_id
#     last_sync_dict = {}
#     metric_mappings = app_configurations.get_app_config()
#     current_datetime = datetime.now(
#         timezone.utc
#     )  # added to ignore the futuristic data points

#     for metric_id in metric_id_list:
#         if metric_id not in metric_mappings:
#             logger.warning("Unrecognized metric_id {}".format(metric_id))
#             return JSONResponse(
#                 status_code=422, content="Unrecognized metric_id."
#             )

#         entity_dict = app_configurations.get_app_config().get(metric_id)
#         collection_name = entity_dict.get("core_entity").get(
#             "underscored_name"
#         )
#         cursor = (
#             mydb[collection_name]
#             .find(
#                 {
#                     "$and": [
#                         {"user_id": user_id},
#                         {"health_device_id": health_device_id},
#                         {"last": {"$lte": current_datetime}},
#                     ]
#                 },
#                 {"_id": 0, "last": 1},
#             )
#             .sort([("last", pymongo.DESCENDING)])
#             .limit(1)
#         )

#         results = list(cursor)

#         if len(results) > 0:
#             end_ts = results[0].get("last")
#             if isinstance(end_ts, str):
#                 # logger.debug("str-last-sync")
#                 last_sync_dict[metric_id] = end_ts
#             if isinstance(end_ts, datetime):
#                 # logger.debug("datetime-last-sync")
#                 end_ts = end_ts.isoformat() + "Z"
#                 last_sync_time = (
#                     parser.parse(end_ts).astimezone(IST_TIMEZONE).isoformat()
#                 )
#                 last_sync_dict[metric_id] = last_sync_time
#         else:
#             last_sync_dict[metric_id] = ""

#     return JSONResponse(status_code=200, content=last_sync_dict)


# @chronos_router.post(
#     "/api/user/link-device", dependencies=[Depends(verify_client)]
# )
# async def user_link_device(
#     body_data: HealthDevice, user_id: str = Header(...)
# ):

#     user_device_mapping = {}
#     health_device_id = body_data.health_device_id
#     health_device_type = body_data.health_device_type
#     health_device_meta = (
#         body_data.health_device_meta.dict()
#         if body_data.health_device_meta
#         else {}
#     )
#     number_of_linked_devices = get_count_of_actively_linked_devices(
#         mydb, USER_DEVICE_MAPPINGS_COLLECTION, user_id
#     )

#     device_already_registered_cursor = mydb[
#         USER_DEVICE_MAPPINGS_COLLECTION
#     ].find(
#         {
#             "$and": [
#                 {"user_id": user_id},
#                 {"health_device_id": health_device_id},
#                 {"device_linked": 1},
#             ]
#         }
#     )

#     if len(list(device_already_registered_cursor)) > 0:
#         return JSONResponse(status_code=200, content="Device already linked.")

#     user_device_mapping = {
#         "user_id": user_id,
#         "health_device_id": health_device_id,
#         "health_device_type": health_device_type,
#         "health_device_meta": health_device_meta,
#     }

#     device_linked_with_cursor = mydb[USER_DEVICE_MAPPINGS_COLLECTION].find(
#         {
#             "$and": [
#                 {"health_device_id": health_device_id},
#                 {"device_linked": 1},
#             ]
#         }
#     )
#     device_linked_with = list(device_linked_with_cursor)

#     if len(device_linked_with) > 0:
#         return JSONResponse(
#             status_code=409, content="Device already linked with another user."
#         )

#     else:
#         any_device_unlinked = False
#         if number_of_linked_devices >= int(MAX_LINKED_DEVICE_LIMIT):
#             any_device_unlinked = unlink_oldest_active_device(
#                 mydb, USER_DEVICE_MAPPINGS_COLLECTION, user_id
#             )

#         user_cursor = mydb[USER_DEVICE_MAPPINGS_COLLECTION].find(
#             {
#                 "$and": [
#                     {"user_id": user_id},
#                     {"health_device_id": health_device_id},
#                 ]
#             }
#         )
#         user_doc = list(user_cursor)
#         user_device_mapping["device_linked"] = 1
#         user_device_mapping["device_saved"] = 1
#         user_device_mapping["device_auto_connect"] = 1

#         if len(user_doc) > 0:
#             updated_at = datetime.utcnow()
#             user_device_mapping["updated_at"] = updated_at
#             user_device_mapping["device_last_linked_at"] = updated_at
#             mydb[USER_DEVICE_MAPPINGS_COLLECTION].update_one(
#                 {"user_id": user_id, "health_device_id": health_device_id},
#                 {"$set": user_device_mapping},
#             )

#         else:
#             created_at = datetime.utcnow()
#             updated_at = created_at
#             user_device_mapping["created_at"] = created_at
#             user_device_mapping["updated_at"] = updated_at
#             user_device_mapping["device_last_linked_at"] = updated_at
#             mydb[USER_DEVICE_MAPPINGS_COLLECTION].insert_one(
#                 user_device_mapping
#             )

#         if any_device_unlinked:
#             return JSONResponse(
#                 status_code=200,
#                 content="Device successfully linked but since you have exceeded the max limit for linked devices, we have automatically unlinked your oldest active device.",
#             )

#         return JSONResponse(
#             status_code=200, content="Device successfully linked."
#         )


# @chronos_router.post(
#     "/api/user/unlink-device", dependencies=[Depends(verify_client)]
# )
# async def user_unlink_device(
#     body_data: HealthDevice, user_id: str = Header(...)
# ):

#     health_device_id = body_data.health_device_id
#     cursor = mydb[USER_DEVICE_MAPPINGS_COLLECTION].find(
#         {
#             "$and": [
#                 {"user_id": user_id},
#                 {"health_device_id": health_device_id},
#                 {"device_linked": 1},
#             ]
#         }
#     )
#     results = list(cursor)

#     if len(results) > 0:
#         for result in results:
#             updated_at = datetime.utcnow()
#             updations = {
#                 "$set": {"device_linked": 0, "updated_at": updated_at}
#             }
#             mydb[USER_DEVICE_MAPPINGS_COLLECTION].update_one(result, updations)
#         return JSONResponse(
#             status_code=200, content="Device successfully unlinked."
#         )
#     else:
#         return JSONResponse(
#             status_code=400,
#             content="Device cannot be unlinked as it is not registered with given user.",
#         )


# @chronos_router.post(
#     "/api/user/unsave-device", dependencies=[Depends(verify_client)]
# )
# async def unsave_device(body_data: HealthDevice, user_id: str = Header(...)):

#     health_device_id = body_data.health_device_id
#     cursor = mydb[USER_DEVICE_MAPPINGS_COLLECTION].find(
#         {
#             "$and": [
#                 {"user_id": user_id},
#                 {"health_device_id": health_device_id},
#             ]
#         }
#     )
#     results = list(cursor)

#     if len(results) > 0:
#         for result in results:
#             updated_at = datetime.utcnow()
#             updations = {
#                 "$set": {
#                     "device_linked": 0,
#                     "device_saved": 0,
#                     "updated_at": updated_at,
#                 }
#             }
#             mydb[USER_DEVICE_MAPPINGS_COLLECTION].update_one(result, updations)
#         return JSONResponse(
#             status_code=200, content="Device unsaved successfully."
#         )
#     else:
#         return JSONResponse(
#             status_code=400,
#             content="Device cannot be unsaved",
#         )


# @chronos_router.put(
#     "/api/user/device-preference", dependencies=[Depends(verify_client)]
# )
# async def update_user_device_preference(
#     body_data: HealthDevicePreference, user_id: str = Header(...)
# ):

#     health_device_id = body_data.health_device_id
#     health_device_meta = body_data.health_device_meta
#     device_auto_connect = body_data.device_auto_connect
#     data_last_synced_at = body_data.data_last_synced_at
#     health_metrics_config_list = body_data.health_metrics_config
#     preferences_dict = {}

#     user_device_mapping_cursor = mydb[USER_DEVICE_MAPPINGS_COLLECTION].find(
#         {
#             "$and": [
#                 {"user_id": user_id},
#                 {"health_device_id": health_device_id},
#                 {"device_linked": 1},
#             ]
#         }
#     )

#     user_device_mapping = list(user_device_mapping_cursor)

#     if len(user_device_mapping) < 1:
#         return JSONResponse(
#             status_code=400, content="Device not linked with the user."
#         )

#     user_device_mapping_dict = user_device_mapping[0]
#     existing_health_device_meta = user_device_mapping_dict.get(
#         "health_device_meta", {}
#     )

#     if device_auto_connect is not None:
#         preferences_dict["device_auto_connect"] = device_auto_connect

#     if data_last_synced_at is not None:
#         preferences_dict["data_last_synced_at"] = data_last_synced_at

#     if health_device_meta is not None:
#         preferences_dict["health_device_meta"] = existing_health_device_meta
#         if health_device_meta.brand is not None:
#             preferences_dict["health_device_meta"].update(
#                 {"brand": health_device_meta.brand}
#             )
#         if health_device_meta.model is not None:
#             preferences_dict["health_device_meta"].update(
#                 {"model": health_device_meta.model}
#             )
#         if health_device_meta.display_name is not None:
#             preferences_dict["health_device_meta"].update(
#                 {"display_name": health_device_meta.display_name}
#             )
#         logger.debug(preferences_dict)

#     if health_metrics_config_list is not None:
#         health_metrics_config = user_device_mapping_dict.get(
#             "health_metrics_config", {}
#         )

#         for health_metric_config in health_metrics_config_list:

#             metric_id = health_metric_config.metric_id
#             entity_dict = app_configurations.get_app_config().get(metric_id)
#             if not entity_dict:
#                 return JSONResponse(
#                     status_code=422, content="Unrecognized metric-id."
#                 )

#             entity_name = entity_dict.get("core_entity").get(
#                 "underscored_name"
#             )
#             config_update_dict = {"entity_id": metric_id}
#             read_metric_data_config = health_metric_config.read_metric_data
#             metric_auto_sync_config = health_metric_config.metric_auto_sync
#             auto_sync_interval_seconds_config = (
#                 health_metric_config.auto_sync_interval_seconds
#             )

#             if read_metric_data_config is not None:
#                 config_update_dict[
#                     "read_metric_data"
#                 ] = read_metric_data_config
#             if metric_auto_sync_config is not None:
#                 config_update_dict[
#                     "metric_auto_sync"
#                 ] = metric_auto_sync_config
#             if auto_sync_interval_seconds_config:
#                 config_update_dict[
#                     "auto_sync_interval_seconds"
#                 ] = auto_sync_interval_seconds_config

#             if entity_name in health_metrics_config:
#                 health_metrics_config[entity_name].update(config_update_dict)
#             else:
#                 health_metrics_config[entity_name] = config_update_dict

#         preferences_dict["health_metrics_config"] = health_metrics_config

#     updated_at = datetime.utcnow()
#     preferences_dict["updated_at"] = updated_at
#     updations = {"$set": preferences_dict}
#     db_response = mydb[USER_DEVICE_MAPPINGS_COLLECTION].update(
#         {"user_id": user_id, "health_device_id": health_device_id}, updations
#     )
#     # logger.debug(db_response)
#     return JSONResponse(
#         status_code=200, content="Device preferences updated successfully."
#     )


# @chronos_router.get("/api/user/linked-devices")
# async def get_user_linked_devices(user_id: str = Header(...)):

#     try:
#         user_device_mapping_collection = mydb[USER_DEVICE_MAPPINGS_COLLECTION]
#         linked_device_cursor = user_device_mapping_collection.find(
#             {"$and": [{"user_id": user_id}, {"device_saved": {"$ne": 0}}]},
#             {"_id": 0, "created_at": 0, "updated_at": 0},
#         )
#     except Exception as exc:
#         logger.error("DB error while fetching linked devices - {}".format(exc))
#         return JSONResponse(
#             status_code=500,
#             content="Could not get linked devices, error - {}".format(exc),
#         )

#     linked_devices = list(linked_device_cursor)
#     health_devices_config = app_configurations.get_health_devices_config()

#     for device_dict in linked_devices:
#         device_meta = (
#             device_dict.get("health_device_meta")
#             if device_dict.get("health_device_meta")
#             else {}
#         )
#         device_brand = device_meta.get("brand", "default")
#         device_specific_config = health_devices_config.get(device_brand, {})
#         device_specific_display_config = device_specific_config.get(
#             "health_devices_config", {}
#         )
#         device_specific_metrics_config = device_specific_config.get(
#             "health_metrics_config", {}
#         )

#         device_model_name = device_specific_display_config.get(
#             "health_device_model", {}
#         ).get("display_name", "")

#         device_type_name = (
#             device_specific_display_config.get("health_device_type", {})
#             .get("health_device_type_core_entity", {})
#             .get("display_name", "")
#         )
#         default_device_display_name = device_specific_display_config.get(
#             "health_device", {}
#         ).get("display_name", "")

#         if "device_saved" not in device_dict:
#             device_dict["device_saved"] = 1

#         if "device_auto_connect" not in device_dict:
#             device_dict["device_auto_connect"] = 1

#         if "device_last_linked_at" in device_dict:
#             device_last_linked_at = device_dict["device_last_linked_at"]
#             if isinstance(device_last_linked_at, datetime):
#                 device_last_linked_at = device_last_linked_at.strftime(
#                     DATETIME_STRING_FORMAT
#                 )
#             device_dict["device_last_linked_at"] = device_last_linked_at
#         else:
#             device_dict["device_last_linked_at"] = ""

#         if "data_last_synced_at" in device_dict:
#             data_last_synced_at = device_dict["data_last_synced_at"]
#             if isinstance(data_last_synced_at, datetime):
#                 data_last_synced_at = data_last_synced_at.strftime(
#                     DATETIME_STRING_FORMAT
#                 )
#             device_dict["data_last_synced_at"] = data_last_synced_at
#         else:
#             device_dict["data_last_synced_at"] = ""

#         if "health_device_type" in device_dict:
#             device_type_db_value = device_dict["health_device_type"]
#             if device_type_db_value is None or device_type_db_value == "":
#                 device_dict["health_device_type"] = device_type_name
#         else:
#             device_dict["health_device_type"] = device_type_name

#         if "health_device_meta" in device_dict:
#             if not device_dict["health_device_meta"]:
#                 device_dict["health_device_meta"] = {}
#             if not device_dict["health_device_meta"].get("display_name"):
#                 device_dict["health_device_meta"][
#                     "display_name"
#                 ] = default_device_display_name

#         health_metrics_db_values = device_dict.get("health_metrics_config", {})
#         restructured_health_metrics_db_values = {}

#         for metric, metric_config in health_metrics_db_values.items():
#             core_entity_id = metric_config.pop("entity_id")
#             if core_entity_id not in restructured_health_metrics_db_values:
#                 restructured_health_metrics_db_values[
#                     core_entity_id
#                 ] = metric_config
#         device_specific_metrics_config.update(
#             restructured_health_metrics_db_values
#         )
#         device_dict["health_metrics_config"] = device_specific_metrics_config

#     return JSONResponse(status_code=200, content=linked_devices)


# @chronos_router.delete(
#     "/api/metric/delete", dependencies=[Depends(verify_client)]
# )
# async def remove_metric_data(body_data: DropData, user_id: str = Header(...)):

#     channel_type = body_data.channel_type
#     if channel_type not in DATA_DELETION_ALLOWED_CHANNELS:
#         logger.warn("Unauthorized data deletion attempted.")
#         return JSONResponse(status_code=400, content="Deletion not allowed.")

#     metric_ids = body_data.metric_id

#     delete_query = {"user_id": user_id, "channel_type": channel_type}
#     number_of_deleted_documents = 0

#     for metric_id in metric_ids:
#         entity_dict = app_configurations.get_app_config().get(metric_id)
#         collection_name = entity_dict.get("core_entity").get(
#             "underscored_name"
#         )
#         collection = mydb[collection_name]
#         data_deletetion = collection.delete_many(delete_query)
#         number_of_deleted_documents += data_deletetion.deleted_count
#     logger.debug("Deleted {} documents.".format(number_of_deleted_documents))
#     if number_of_deleted_documents > 0:
#         return JSONResponse(
#             status_code=200, content="Data deleted successfully."
#         )
#     return JSONResponse(status_code=200, content="No data to delete.")


# @chronos_router.post(
#     "/api/metric/read-aggregated", dependencies=[Depends(verify_client)]
# )
# async def read_aggregated_metric_event(
#     body_data: FetchAggregatedData, user_id: str = Header(...)
# ):

#     health_device_id_list = body_data.health_device_ids
#     start_datetime = parser.parse(body_data.start_datetime)
#     end_datetime = parser.parse(body_data.end_datetime)
#     metric_id = body_data.metric_id
#     bucket_seconds = body_data.bucket_seconds
#     data_sources = body_data.data_sources
#     multi_source_aggregation = body_data.multi_source_aggregation

#     total_seconds = end_datetime - start_datetime
#     total_seconds = total_seconds.total_seconds()
#     days = total_seconds // DAY_SECONDS

#     if end_datetime <= start_datetime:
#         return JSONResponse(
#             status_code=400,
#             content="End datetime cannot be <= start datetime.",
#         )

#     if days > MAX_DAYS:
#         return JSONResponse(
#             status_code=400,
#             content="Datetime range cannot exceed {} days.".format(MAX_DAYS),
#         )

#     if bucket_seconds:
#         if bucket_seconds > total_seconds:
#             return JSONResponse(
#                 status_code=400,
#                 content="Bucket seconds cannot be greater than entire datetime range",
#             )

#         if bucket_seconds < MIN_BUCKET_SECONDS:
#             return JSONResponse(
#                 status_code=400,
#                 content="Bucket seconds cannot be less than {}.".format(
#                     MIN_BUCKET_SECONDS
#                 ),
#             )
#         total_buckets = total_seconds // bucket_seconds
#         if total_buckets > MAX_NUMBER_OF_BUCKETS:
#             return JSONResponse(
#                 status_code=400,
#                 content="Total buckets cannot exceed {}.".format(
#                     MAX_NUMBER_OF_BUCKETS
#                 ),
#             )

#     bucket_boundaries = []
#     if not bucket_seconds:
#         bucket_seconds = total_seconds
#         bucket_boundaries = [start_datetime, end_datetime]
#     else:
#         start = start_datetime
#         while start <= end_datetime:
#             bucket_boundaries.append(start)
#             start = start + timedelta(seconds=bucket_seconds)
#     # logger.debug(bucket_boundaries)

#     entity_dict = app_configurations.get_app_config().get(metric_id)
#     if not entity_dict:
#         return JSONResponse(status_code=422, content="Unrecognized metric-id.")

#     aggregation_config = entity_dict.get("aggregation")
#     if not aggregation_config:
#         return JSONResponse(
#             status_code=422, content="Aggregation config not found."
#         )

#     if multi_source_aggregation:
#         response = {"data": {metric_id: []}}
#     else:
#         response = {"data": {metric_id: {}}}

#     combined_device_data_points = []
#     if "all" in data_sources or "device" in data_sources:
#         collection_name = entity_dict.get("core_entity").get(
#             "underscored_name"
#         )
#         collection = mydb[collection_name]

#         data_fetch_query = get_aggregated_device_data_query(
#             user_id,
#             health_device_id_list,
#             start_datetime,
#             end_datetime,
#             bucket_boundaries,
#             aggregation_config,
#             multi_source_aggregation,
#         )

#         device_data_points = list(
#             collection.aggregate(
#                 pipeline=data_fetch_query,
#                 hint={
#                     "user_id": 1,
#                     "health_device_id": -1,
#                     "samples.start_time": -1,
#                 },
#             )
#         )
#         # logger.debug(device_data_points)

#         if multi_source_aggregation:
#             combined_device_data_points = (
#                 restructure_data_points_combined_devices(device_data_points)
#             )
#         else:
#             response["data"][metric_id].update(
#                 restructure_data_points_individual_devices(device_data_points)
#             )

#     if (
#         "all" in data_sources
#         or "user" in data_sources
#         or "provider" in data_sources
#     ):
#         ditto_entities = ditto_get_entity_by_data_source(user_id, body_data)
#         if ditto_entities:
#             ditto_entities_list = ditto_entities.json()["values"]

#     aggregated_user_data_list = []
#     if "all" in data_sources or "user" in data_sources:
#         if ditto_entities_list != []:
#             manual_df = pd.DataFrame(data=ditto_entities_list)
#             manual_df = manual_df[manual_df.data_source == "user"]
#             manual_df = manual_df.set_index(["datetime"])
#             manual_df.index = pd.to_datetime(manual_df.index)
#             manual_df.value = pd.to_numeric(
#                 manual_df.value, errors="coerce"
#             ).fillna(0)
#             manual_df = manual_df[manual_df.value > 0]
#             grouping_minutes = str(round(bucket_seconds // 60)) + "min"
#             grouped_manual_df = manual_df.groupby(
#                 pd.Grouper(
#                     freq=grouping_minutes, origin=body_data.start_datetime
#                 )
#             )
#             aggregated_df = aggregate_datetime_grouped_data(
#                 grouped_manual_df,
#                 aggregation_config.get("aggregator").get("name"),
#             )
#             aggregated_df = aggregated_df[aggregated_df.value != 0]

#             other_aggregations_df = grouped_manual_df["value"].agg(
#                 ["min", "max", "mean"]
#             )
#             other_aggregations_df = other_aggregations_df.dropna()

#             all_aggregations_df = pd.concat(
#                 [aggregated_df, other_aggregations_df], axis=1
#             )
#             all_aggregations_df = all_aggregations_df.dropna()
#             all_aggregations_df.index = all_aggregations_df.index.map(
#                 lambda x: datetime.strftime(x, DATETIME_STRING_FORMAT)
#             )
#             all_aggregations_df.rename(
#                 columns={
#                     "value": "aggregated_value",
#                     "min": "min_value",
#                     "max": "max_value",
#                     "mean": "avg_value",
#                 },
#                 inplace=True,
#             )
#             all_aggregations_df = all_aggregations_df.reset_index()
#             aggregated_user_data_list += all_aggregations_df.to_dict(
#                 orient="records"
#             )
#             # logger.debug(aggregated_user_data_list)

#             if not multi_source_aggregation:
#                 response["data"][metric_id].update(
#                     {"user": aggregated_user_data_list}
#                 )

#     aggregated_provider_data_list = []
#     if "all" in data_sources or "provider" in data_sources:
#         if ditto_entities_list != []:
#             provider_df = pd.DataFrame(data=ditto_entities_list)
#             provider_df = provider_df[provider_df.data_source == "provider"]
#             provider_df = provider_df.set_index(["datetime"])
#             provider_df.index = pd.to_datetime(provider_df.index)
#             provider_df.value = pd.to_numeric(
#                 provider_df.value, errors="coerce"
#             ).fillna(0)
#             provider_df = provider_df[provider_df.value > 0]
#             grouping_minutes = str(round(bucket_seconds // 60)) + "min"
#             grouped_provider_df = provider_df.groupby(
#                 pd.Grouper(
#                     freq=grouping_minutes, origin=body_data.start_datetime
#                 )
#             )
#             aggregated_df = aggregate_datetime_grouped_data(
#                 grouped_provider_df,
#                 aggregation_config.get("aggregator").get("name"),
#             )
#             aggregated_df = aggregated_df[aggregated_df.value != 0]
#             other_aggregations_df = grouped_provider_df["value"].agg(
#                 ["min", "max", "mean"]
#             )
#             other_aggregations_df = other_aggregations_df.dropna()
#             all_aggregations_df = pd.concat(
#                 [aggregated_df, other_aggregations_df], axis=1
#             )
#             all_aggregations_df = all_aggregations_df.dropna()
#             all_aggregations_df.index = all_aggregations_df.index.map(
#                 lambda x: datetime.strftime(x, DATETIME_STRING_FORMAT)
#             )
#             all_aggregations_df.rename(
#                 columns={
#                     "value": "aggregated_value",
#                     "min": "min_value",
#                     "max": "max_value",
#                     "mean": "avg_value",
#                 },
#                 inplace=True,
#             )
#             all_aggregations_df = all_aggregations_df.reset_index()
#             aggregated_provider_data_list += all_aggregations_df.to_dict(
#                 orient="records"
#             )

#             if not multi_source_aggregation:
#                 response["data"][metric_id].update(
#                     {"provider": aggregated_provider_data_list}
#                 )

#     aggregated_all_source_data_list = []
#     if multi_source_aggregation:
#         all_source_data_points = (
#             combined_device_data_points
#             + aggregated_user_data_list
#             + aggregated_provider_data_list
#         )

#         if all_source_data_points == []:
#             return JSONResponse(status_code=200, content=response)

#         all_source_df = pd.DataFrame(data=all_source_data_points)
#         all_source_df = all_source_df[["datetime", "aggregated_value"]]
#         all_source_df = all_source_df.set_index(["datetime"])
#         all_source_df.index = pd.to_datetime(all_source_df.index)
#         grouped_all_source_df = all_source_df.groupby(all_source_df.index)
#         aggregated_all_source_df = aggregate_datetime_grouped_data(
#             grouped_all_source_df,
#             aggregation_config.get("multiple_device_logic").get("name"),
#         )

#         other_aggs_all_source_df = grouped_all_source_df[
#             "aggregated_value"
#         ].agg(["min", "max", "mean"])
#         all_aggs_all_source_df = pd.concat(
#             [aggregated_all_source_df, other_aggs_all_source_df], axis=1
#         )
#         all_aggs_all_source_df = all_aggs_all_source_df.dropna()
#         all_aggs_all_source_df.index = all_aggs_all_source_df.index.map(
#             lambda x: datetime.strftime(x, DATETIME_STRING_FORMAT)
#         )
#         all_aggs_all_source_df.rename(
#             columns={
#                 "min": "min_value",
#                 "max": "max_value",
#                 "mean": "avg_value",
#             },
#             inplace=True,
#         )
#         all_aggs_all_source_df = all_aggs_all_source_df.reset_index()
#         aggregated_all_source_data_list += all_aggs_all_source_df.to_dict(
#             orient="records"
#         )
#         # logger.debug(aggregated_all_source_data_list)
#         response["data"][metric_id] += aggregated_all_source_data_list
#         return JSONResponse(status_code=200, content=response)
#     else:
#         return JSONResponse(status_code=200, content=response)


# @chronos_router.post(
#     "/api/metric/read-latest", dependencies=[Depends(verify_client)]
# )
# async def read_latest_metric_event(
#     body_data: FetchLatestData, user_id: str = Header(...)
# ):
#     response = {"data": {}}
#     metric_ids = body_data.metric_ids
#     data_sources = body_data.data_sources
#     health_device_ids = body_data.health_device_ids

#     ditto_entities_dict = {}
#     if (
#         "all" in data_sources
#         or "user" in data_sources
#         or "provider" in data_sources
#     ):
#         ditto_entities_dict = {}
#         ditto_response = ditto_get_entities(user_id, body_data)
#         if ditto_response:
#             ditto_entities = ditto_response.json()["entities"]
#         if ditto_response != []:
#             for entity in ditto_entities:
#                 sample = {}
#                 sample["datetime"] = entity.get("data").get("datetime")
#                 sample["value"] = entity.get("data").get("value", 0)
#                 sample["data_source"] = entity.get("data").get("data_source")
#                 ditto_entities_dict[entity.get("entity_id")] = sample
#         # logger.debug(ditto_entities_dict)

#     device_data_points_dict = {}
#     if "all" in data_sources or "device" in data_sources:
#         latest_data_point_query = get_latest_device_data_point_query(
#             user_id, health_device_ids
#         )
#         device_data_points_dict = {}
#         for metric_id in metric_ids:
#             entity_dict = app_configurations.get_app_config().get(metric_id)
#             if not entity_dict:
#                 continue
#                 # return JSONResponse(
#                 #     status_code=400, content="Unrecognized metric-id"
#                 # )
#             collection_name = entity_dict.get("core_entity").get(
#                 "underscored_name"
#             )
#             collection = mydb[collection_name]
#             result = list(collection.aggregate(latest_data_point_query))
#             device_data_points_dict[metric_id] = {}
#             if len(result) > 0:
#                 device_data_points_dict[metric_id] = result[0]
#                 metric_datetime = device_data_points_dict[metric_id][
#                     "datetime"
#                 ]
#                 if isinstance(metric_datetime, datetime):
#                     metric_datetime_str = metric_datetime.strftime(
#                         DATETIME_STRING_FORMAT
#                     )
#                 elif isinstance(metric_datetime, str):
#                     d = parser.parse(metric_datetime).astimezone(tz.UTC)
#                     metric_datetime_str = d.strftime(DATETIME_STRING_FORMAT)
#                 else:
#                     metric_datetime_str = ""
#                 device_data_points_dict[metric_id][
#                     "datetime"
#                 ] = metric_datetime_str
#         # logger.debug(device_data_points_dict)

#     final_dict = {}
#     for metric in metric_ids:
#         data_point = {}
#         if metric in ditto_entities_dict:
#             data_point = ditto_entities_dict[metric]
#         if metric in device_data_points_dict:
#             data_point = device_data_points_dict[metric]
#         if metric in ditto_entities_dict and metric in device_data_points_dict:
#             if ditto_entities_dict[metric].get(
#                 "datetime", ""
#             ) >= device_data_points_dict[metric].get("datetime", ""):
#                 data_point = ditto_entities_dict[metric]
#             else:
#                 data_point = device_data_points_dict[metric]
#         final_dict[metric] = data_point
#         response["data"] = final_dict
#     return JSONResponse(status_code=200, content=response)


# @chronos_router.post("/api/metric/read", dependencies=[Depends(verify_client)])
# async def read_metric_event(request: FetchRawData, user_id: str = Header(...)):

#     health_device_id_list = request.health_device_ids
#     data_sources = request.data_sources
#     start_datetime = parser.parse(request.start_datetime)
#     end_datetime = parser.parse(request.end_datetime)
#     metric_id = request.metric_id
#     multi_source_aggregation = request.multi_source_aggregation
#     skip = request.skip
#     limit = request.limit

#     entity_dict = app_configurations.get_app_config().get(metric_id)
#     if not entity_dict:
#         return JSONResponse(status_code=422, content="Unrecognized metric-id")
#     collection_name = entity_dict.get("core_entity").get("underscored_name")
#     collection = mydb[collection_name]
#     results = {"data": {}}

#     if "all" in data_sources or "device" in data_sources:

#         device_data_fetch_query = get_raw_device_data_query(
#             user_id,
#             health_device_id_list,
#             start_datetime,
#             end_datetime,
#             skip,
#             limit,
#         )

#         device_data_points = list(
#             collection.aggregate(
#                 pipeline=device_data_fetch_query,
#                 hint={
#                     "user_id": 1,
#                     "health_device_id": -1,
#                     "samples.start_time": -1,
#                 },
#             )
#         )
#         logger.debug("Fetched {} data points.".format(len(device_data_points)))

#         if not multi_source_aggregation:
#             d = defaultdict(list)
#             for item in device_data_points:
#                 data_point_datetime = item["datetime"]
#                 if isinstance(data_point_datetime, datetime):
#                     data_point_datetime_str = data_point_datetime.strftime(
#                         DATETIME_STRING_FORMAT
#                     )
#                 elif isinstance(data_point_datetime, str):
#                     dt = parser.parse(data_point_datetime).astimezone(tz.UTC)
#                     data_point_datetime_str = dt.strftime(
#                         DATETIME_STRING_FORMAT
#                     )
#                 else:
#                     data_point_datetime_str = ""
#                 item["datetime"] = data_point_datetime_str
#                 d[item["health_device_id"]].append(
#                     {
#                         "datetime": item.get("datetime"),
#                         "value": item.get("value"),
#                     }
#                 )
#             results["data"][metric_id] = dict(d)
#         else:
#             # logger.debug(device_data_points)
#             results["data"][metric_id] = []
#             for d in device_data_points:
#                 d["source"] = d.pop("health_device_id")
#                 datetime_obj = d["datetime"]
#                 d["datetime"] = datetime_obj.strftime(DATETIME_STRING_FORMAT)
#             results["data"][metric_id] = device_data_points

#     if "all" in data_sources or "manual" in data_sources:
#         ditto_response = ditto_get_entity_by_data_source(
#             user_id, request, data_source="user"
#         )
#         manual_data_points = ditto_response.json()["values"]

#         if not multi_source_aggregation:
#             manual_data_list = []
#             for point in manual_data_points:
#                 sample = {}
#                 sample["datetime"] = point["datetime"]
#                 sample["value"] = float(point["value"])
#                 manual_data_list.append(sample)
#             results["data"][metric_id]["user"] = manual_data_list
#         else:
#             manual_data_list = []
#             for point in manual_data_points:
#                 sample = {}
#                 sample["datetime"] = point["datetime"]
#                 sample["value"] = float(point["value"])
#                 sample["source"] = "user"
#                 manual_data_list.append(sample)
#             results["data"][metric_id] += manual_data_list

#     if "all" in data_sources or "provider" in data_sources:
#         ditto_provider_response = ditto_get_entity_by_data_source(
#             user_id, request, data_source="provider"
#         )
#         provider_data_points = ditto_provider_response.json()["values"]

#         if not multi_source_aggregation:
#             provider_data_list = []
#             for point in provider_data_points:
#                 sample = {}
#                 sample["datetime"] = point["datetime"]
#                 sample["value"] = float(point["value"])
#                 provider_data_list.append(sample)
#             results["data"][metric_id]["provider"] = provider_data_list
#         else:
#             provider_data_list = []
#             for point in provider_data_points:
#                 sample = {}
#                 sample["datetime"] = point["datetime"]
#                 sample["value"] = float(point["value"])
#                 sample["source"] = "provider"
#                 provider_data_list.append(sample)
#             results["data"][metric_id] += provider_data_list

#     return results
