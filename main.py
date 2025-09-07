"""
Production Trading API Infrastructure - Code Sample

Note: This is a partial implementation showing core architecture patterns.
Some helper functions and dependencies are imported from other modules
in the production system.
"""

import os, logging, aiohttp, asyncio, redis, hmac, time, json, base64, httpx, models
from collections import OrderedDict
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, Request
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from helper import *


load_dotenv()
API_KEY = os.environ.get("API_KEY")
app = FastAPI()

configure_logging()
logger = logging.getLogger(__name__)
models.Base.metadata.create_all(bind=engine)

# Main api check
IS_MAIN_API = os.environ.get('MAIN_API', 'false').lower() in ['true', '1', 'yes', 'on']


scheduler = AsyncIOScheduler()
# Global cancellation event if an alert comes in, skip the scheduler.
CANCEL_SCHEDULER = asyncio.Event()

## HIGH FREQUENCY ENDPOINT ////////////////////
@app.post("/tradingview_webhook_endpoint_example")  
async def tradingview_webhook(request: Request, db: Session = Depends(get_db),ip: str = Depends(verify_ip_whitelist)):

    global MAIN_PROCESSING_ACTIVE, ALERT_RECEIVED, LAST_ALERT_BODY, INCOMING_TRADES, HF_REQUEST

    # ...

    body = await request.body()
    LAST_ALERT_BODY = body
    message = body.decode("utf-8")
    parsed_data = await parse_trade_message(message)
    
    if not parsed_data:
        logger.warning(f"Invalid high-frequency trade message received")
        raise HTTPException(status_code=400, detail="Invalid message format")

    if parsed_data["api_key"] != API_KEY:
        logger.warning(f"Incorrect key received")
        return 
    
    # ...


# Global cancellation event
CANCEL_SCHEDULER = asyncio.Event()

async def scheduled_hf_with_delay():
    
    """Internal scheduler - check for Pine alerts, run HF if none recent"""

    global MAIN_PROCESSING_ACTIVE, trail_stop_system

    logger.info(" scheduler function")

    if trail_stop_system:
        await trail_stop_system.pause_for_candle()

    try:
        
        MAIN_PROCESSING_ACTIVE = True
        
        # Wait 30 seconds with cancellation check every second
        # Dont run scheduler if an alert came in
        for i in range(30):
            if CANCEL_SCHEDULER.is_set():
                logger.info("Scheduler execution cancelled manually")
                CANCEL_SCHEDULER.clear()  # Reset for next time
                return
            await asyncio.sleep(1)

    # ...

    except Exception as e:
        logger.error(f"Scheduled HF failed: {e}")
        # Reset even on error to prevent stuck state  Only scheduler resets this.

    finally:
        MAIN_PROCESSING_ACTIVE = False


@app.get("/health_endpoint")
async def health(request: Request, db: Session = Depends(get_db),ip: str = Depends(verify_ip_whitelist)):
    logger.info(f"Received health check request from IP: {request.client.host}")
    return {"status": "healthy", "message": "Server is running."}

redis_client = None # Example

if redis_client:
    app.add_middleware(
        RedisRateLimitMiddleware,
        redis_client=redis_client,
        limit = 5,  # Number of requests available
        window = 60 # Time window in seconds (1 minute)
    )
    logger.info(f"✅ Rate limiting middleware initialized: {5} requests per {60} seconds")
else:
    logger.warning("⚠️ Rate limiting is disabled due to Redis connection issues")


@app.on_event("startup")
async def startup_db_client():
    
    initialize_database()  
    
    # Hide the regular scheduler schedule and scheduler complete logs to reduce clutter.
    logging.getLogger('apscheduler.schedulers.base').setLevel(logging.ERROR)    
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
    setup_global_exception_handler()


## Trade logic file

class BitgetTrader:
    def __init__(self, api_key: str, api_secret: str, passphrase: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.base_url = "https://api.bitget.com"

    def _generate_signature(self, timestamp: str, method: str, request_path: str, query_string: str = "", body: str = "") -> str:
        # Construct message string
        if query_string and "?" not in request_path:
            message = timestamp + method.upper() + request_path + "?" + query_string + body
        else:
            message = timestamp + method.upper() + request_path + body
        
        new_val = self.api_secret.strip()  # Remove any whitespace
        if "=" in new_val:  # Remove trailing equals signs if present
            new_val = new_val.rstrip("=")
        signature = base64.b64encode(
            hmac.new(
                new_val.encode('utf-8'),
                message.encode('utf-8'),
                digestmod='sha256'
            ).digest()
        ).decode('utf-8')  # Decode bytes to string
        
        return signature


    def _parse_params_to_str(self, params):
        if not params:
            return ""
            
        # Convert params to list of tuples and sort by key
        param_list = [(str(key), str(value)) for key, value in params.items()]
        param_list.sort(key=lambda x: x[0])

        return "&".join([f"{key}={value}" for key, value in param_list])


    async def _make_request(self, method: str, endpoint: str, params: dict = None, data: dict = None):

        """Helper method to make authenticated requests"""
        timestamp = str(int(time.time() * 1000))

        # Format query string for signature
        query_string = self._parse_params_to_str(params) if params else ""
        
        body_str = ""
        if method == "POST" and data:
            body_str = json.dumps(data, separators=(',', ':'))  # Use compact JSON formatting
        
        # Generate signature WITH the body for POST requests
        signature = self._generate_signature(timestamp, method, endpoint, query_string, body_str)

        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-PASSPHRASE": self.passphrase,
            "ACCESS-TIMESTAMP": timestamp,
            "locale": "en-US",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        # Create ordered parameters dictionary to ensure same order as in signature
        ordered_params = None
        if params:
            # Create an OrderedDict with keys sorted alphabetically
            from collections import OrderedDict
            param_list = [(key, params[key]) for key in sorted(params.keys())]
            ordered_params = OrderedDict(param_list)

        async with httpx.AsyncClient() as client:
            if method == "GET":
                # Use the ordered_params to ensure same parameter order as in signature
                response = await client.get(url, headers=headers, params=ordered_params)
            elif method == "POST":

                response = await client.post(url, headers=headers, json=data)
            
            # Always return the JSON response, let calling functions handle error codes
            try:
                return response.json()
            except:
                # If JSON parsing fails, then raise the original error
                raise Exception(f"API Error: {response.text}")


    async def place_trade(self, 
                          
                         symbol: str = "BTCUSDT", 
                         side: str = "buy",  # "buy" or "sell"
                         trade_side: str = "open",  # "open" or "close"
                         size: str = "0.001",
                         price: str = None,  # Limit price - if None, will be market order
                         product_type: str = "USDT-FUTURES",
                         trade_name: str = "Default"):
        """Place a trade with the specified direction and quantity"""
        try:
            endpoint = "/api/v2/mix/order/place-order" 
            client_oid = f"fastapi_{int(time.time() * 1000)}"
            
            order_data = {
                "symbol":      symbol,
                "productType": product_type,
                "marginMode": "isolated", # Other mode is crossed
                "marginCoin": "USDT",
                "size": size,
                "side": side,
                "tradeSide": trade_side,
                "orderType": "limit" if price else "market",
                "force": "gtc",  # Good till canceled
                "clientOid": client_oid,
                "reduceOnly": "NO"
            }
            
            # Add price if it's a limit order
            if price:
                order_data["price"] = str(price)
            
            result = await self._make_request("POST", endpoint, data=order_data)

        except Exception as e:
            logger.error(f"Error placing trade: {str(e)}.  Instance Number {INSTANCE}")
            send_user_alert(f"Error in trade execution. {side} : {size}. {trade_name}.  Instance Number {INSTANCE}")
            return e # ...