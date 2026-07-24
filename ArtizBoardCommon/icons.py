"""Material Design Icons — centralized icon constants for ArtizBoard.

Flet uses `ft.icons` (Material icons) natively. This module provides:
1. Semantic aliases matching LarcCommon icon names
2. A helper to resolve icon names with proper sizing

Usage:
    ft.Icon(name=icons.PERSON)
    ft.IconButton(icon=icons.ARROW_BACK)
"""

# ── Semantic aliases matching LarcCommon icons.py naming ──

# Theme / Display
LIGHT_MODE = "light_mode"
DARK_MODE = "dark_mode"
CONTRAST = "contrast"
TONALITY = "tonality"
BRIGHTNESS_6 = "brightness_6"

# Navigation
ARROW_BACK = "arrow_back"
ARROW_FORWARD = "arrow_forward"
MENU = "menu"
CLOSE = "close"
HOME = "home"
SEARCH = "search"
PERSON = "person"
SETTINGS = "settings"
LOGOUT = "logout"
DASHBOARD = "dashboard"
FILTER_LIST = "filter_list"

# Actions
ADD = "add"
EDIT = "edit"
DELETE = "delete"
SAVE = "save"
REFRESH = "refresh"
CHECK = "check"
CANCEL = "cancel"
PRINT = "print"
SHARE = "share"
DOWNLOAD = "download"
UPLOAD = "upload"
CONTENT_COPY = "content_copy"

# Status
CHECK_CIRCLE = "check_circle"
ERROR = "error"
WARNING = "warning"
INFO = "info"
SYNC = "sync"
LOCK = "lock"
SCHEDULE = "schedule"
EVENT = "event"
TIMER = "timer"
CALENDAR_TODAY = "calendar_today"

# Network
CLOUD = "cloud"
WIFI = "wifi"
WIFI_OFF = "wifi_off"
STORAGE = "storage"

# Business
SHOPPING_CART = "shopping_cart"
POINT_OF_SALE = "point_of_sale"
RECEIPT = "receipt"
DESCRIPTION = "description"
INVENTORY = "inventory"
CATEGORY = "category"
STAR = "star"
STAR_BORDER = "star_border"
LOCATION_ON = "location_on"
PHONE = "phone"
EMAIL = "email"
LANGUAGE = "language"
VISIBILITY = "visibility"
VISIBILITY_OFF = "visibility_off"

# Layout
VIEW_MODULE = "view_module"
VIEW_LIST = "view_list"
VIEW_COMFY = "view_comfy"
SUBJECT = "subject"
SPACE_DASHBOARD = "space_dashboard"

# Food / Restaurant
RESTAURANT = "restaurant"
RESTAURANT_MENU = "restaurant_menu"
ROOM_SERVICE = "room_service"
DINING = "dining"
LOCAL_PIZZA = "local_pizza"
LOCAL_DINING = "local_dining"
LUNCH_DINING = "lunch_dining"
SET_MEAL = "set_meal"
BAKERY_DINING = "bakery_dining"
TABLE_BAR = "table_bar"
TABLE_RESTAURANT = "table_restaurant"

# Store
STOREFRONT = "storefront"
SHOP = "shop"
SHOP_TWO = "shop_two"
LOCAL_GROCERY_STORE = "local_grocery_store"
LOCAL_MALL = "local_mall"

# Payment
PAYMENTS = "payments"
ACCOUNT_BALANCE = "account_balance"
CREDIT_CARD = "credit_card"
MONEY = "money"
CURRENCY_EXCHANGE = "currency_exchange"
Qr_CODE = "qr_code"

# Personnel
BADGE = "badge"
GROUPS = "groups"
MANAGE_ACCOUNTS = "manage_accounts"
ADMIN_PANEL_SETTINGS = "admin_panel_settings"
ASSIGNMENT_IND = "assignment_ind"

# Charts / Analytics
BAR_CHART = "bar_chart"
PIE_CHART = "pie_chart"
SHOW_CHART = "show_chart"
TRENDING_UP = "trending_up"
TRENDING_DOWN = "trending_down"
ANALYTICS = "analytics"
INSIGHTS = "insights"

# Delivery
LOCAL_SHIPPING = "local_shipping"
DELIVERY_DINING = "delivery_dining"
TWO_WHEELER = "two_wheeler"
PEDAL_BIKE = "pedal_bike"

# Files
FOLDER = "folder"
FOLDER_OPEN = "folder_open"
ATTACH_FILE = "attach_file"
PICTURE_AS_PDF = "picture_as_pdf"
TABLE_CHART = "table_chart"
FILE_PRESENT = "file_present"
SIM_CARD_DOWNLOAD = "sim_card_download"


def resolve(name: str) -> str:
    """Resolve a short semantic name to a Material icon code.

    Supports both semantic names (e.g. 'person') and full Material codes.
    This is a compatibility layer; most icons are used directly as ft.icons.XXX.
    """
    return name
