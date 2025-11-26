"""
Cấu hình cho bot theo dõi giá coin và phân tích thị trường.

Module này chứa tất cả các cấu hình, constants và danh sách coin
được sử dụng trong toàn bộ ứng dụng.
"""

# ===== Cấu hình Telegram =====
TELEGRAM_BOT_TOKEN = '7854015705:AAGvt0T7D-V0iEtq0i5SSw_E7fzMXCTdP1E'
TELEGRAM_CHAT_ID = '@livingcoinpricechannel'
TELEGRAM_SIGNAL_CHAT_ID = '@ftlssignalzhan'  # Channel riêng cho tín hiệu long/short

# ===== Cấu hình API =====
YOUR_CMC_API_KEY = '31ad5461-3d37-4532-89b2-f3df2b096c68'
URL_FNG = 'https://api.alternative.me/fng/'

# ===== Danh sách coin =====
# Key: Symbol trên Binance, Value: Tên hiển thị
COINS = {
    'BTCUSDT': 'BTC',
    'ETHUSDT': 'ETH',
    'SOLUSDT': 'SOL',
    'FETUSDT': 'FET',
    'ALTUSDT': 'ALT',
    'BNBUSDT': 'BNB',
    'NEARUSDT': 'NEAR',
    'LINKUSDT': 'LINK',
    'STRKUSDT': 'STRK',
    'ADAUSDT': 'ADA',
}

# ===== Cấu hình Timezone =====
import pytz
TZ = pytz.timezone('Asia/Bangkok')

# ===== Cấu hình File =====
HISTORY_FILE = 'market_history.csv'

# ===== Cấu hình Signal =====
# Thời gian chờ trước khi phát lại tín hiệu cùng loại (giây)
SIGNAL_COOLDOWN = 6 * 3600  # 6 giờ

# Ngưỡng thay đổi giá trị để phát lại tín hiệu (40%)
SIGNAL_VALUE_THRESHOLD = 0.4

# ===== Cấu hình độ chính xác =====
# Điểm xác nhận tối thiểu để phát tín hiệu (cần ít nhất 2 chỉ báo đồng thuận)
MIN_CONFIRMATION_SCORE = 2

# Điểm xác nhận tối thiểu khi có technical analysis confirmation
MIN_CONFIRMATION_WITH_TECH = 1.5

# Số khung thời gian cần xác nhận xu hướng
TREND_CONFIRMATION_PERIODS = 3

