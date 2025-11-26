"""
Bot theo dõi giá coin và phân tích thị trường.

Bot này:
- Theo dõi giá các coin trên Binance
- Phân tích BTC Dominance, USDT Dominance, Fear & Greed Index
- Phát hiện tín hiệu giao dịch long/short dựa trên phân tích kỹ thuật
- Gửi cảnh báo và tín hiệu qua Telegram
"""

import time
import datetime
import config
import utils
import market_analysis


def main():
    """
    Hàm main chạy bot liên tục:
    - Cập nhật Fear & Greed Index mỗi ngày
    - Cập nhật Dominance mỗi 5 phút
    - Cập nhật giá coin mỗi 30 giây
    - Phát hiện và gửi tín hiệu giao dịch
    """
    last_fng_date = None
    last_dom_time = 0
    fear_index = None
    fear_label = None
    
    while True:
        now = datetime.datetime.now(config.TZ)
        now_ts = int(time.time())
        today = now.date()
        
        # Cập nhật Fear & Greed Index mỗi ngày
        if last_fng_date != today:
            f_index, f_label, f_ts = utils.get_fear_and_greed()
            if f_index is not None:
                fear_index, fear_label = f_index, f_label
                msg = f"📊 <b>Fear & Greed Index:</b> {fear_index} ({fear_label})\n⏱ {utils.format_time(f_ts)}"
                utils.send_telegram_message(msg)
                last_fng_date = today
        
        # Cập nhật Dominance mỗi 5 phút
        if now_ts - last_dom_time >= 300:
            btc_dom, total_market_cap = utils.get_btc_dominance_and_total_marketcap(config.YOUR_CMC_API_KEY)
            usdt_market_cap = utils.get_usdt_market_cap(config.YOUR_CMC_API_KEY)
            usdt_dom = utils.get_usdt_dominance(usdt_market_cap, total_market_cap)
            
            if btc_dom is not None and usdt_dom is not None:
                msg = f"📈 <b>Dominance:</b>\nBTC: {btc_dom:.3f}% | USDT: {usdt_dom:.3f}%"
                utils.send_telegram_message(msg)
                
                # Phân tích thị trường và đưa ra nhận định
                if fear_index is not None:
                    analysis = market_analysis.analyze_market(btc_dom, usdt_dom, fear_index, fear_label)
                    utils.send_telegram_message("🧠 <b>Nhận định thị trường:</b>\n" + analysis)
                
                # Phát hiện tín hiệu giao dịch
                alerts, trading_signals = market_analysis.detect_strong_market_move(btc_dom, usdt_dom, fear_index)
                
                # Gửi alerts thông thường vào channel chính
                for alert in alerts:
                    utils.send_telegram_message(alert)
                
                # Gửi tín hiệu long/short vào channel riêng
                for signal in trading_signals:
                    technical_details = signal.get('technical_details', None)
                    signal_message = utils.format_trading_signal(signal, btc_dom, usdt_dom, fear_index, technical_details)
                    utils.send_signal_message(signal_message)
                
                # Lưu lịch sử thị trường
                utils.save_market_history(now_ts, btc_dom, usdt_dom, fear_index)
                last_dom_time = now_ts

        # Cập nhật giá coin mỗi 30 giây
        price_msg = "💰 <b>Giá coin cập nhật:</b>\n"

        for sym in config.COINS:
            price = utils.get_price_binance(sym)
            if price is not None:
                price_msg += f"{config.COINS[sym]}: {price:.3f} | "
                utils.price_history[sym].append((now_ts, price))
                utils.price_history[sym] = utils.price_history[sym][-100:]  # Giữ 100 điểm gần nhất
                
                # Phát hiện biến động giá mạnh
                alert = utils.detect_price_spike(sym)
                if alert:
                    utils.send_telegram_message("🚨 <b>Cảnh báo biến động giá:</b>\n" + alert)

        price_msg = price_msg.rstrip(" | ")
        if price_msg:
            utils.send_telegram_message(price_msg)

        time.sleep(30)


if __name__ == "__main__":
    main()
