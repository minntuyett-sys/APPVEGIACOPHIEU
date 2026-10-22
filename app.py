import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date, timedelta

# ==========================================
# 1. CẤU HÌNH TRANG STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Phân tích giá cổ phiếu",
    page_icon="📈",
    layout="wide"
)

st.title("📈 ỨNG DỤNG PHÂN TÍCH GIÁ CỔ PHIẾU")
st.markdown(
    "Nhập mã cổ phiếu và khoảng thời gian để xem "
    "biểu đồ giá đóng cửa cùng thông tin giá gần nhất."
)

# ==========================================
# 2. GIAO DIỆN NHẬP DỮ LIỆU
# ==========================================
with st.form("stock_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        ticker = st.text_input(
            "Mã cổ phiếu",
            value="VNM.VN",
            help="Ví dụ: VNM.VN, FPT.VN, VCB.VN, AAPL"
        ).strip().upper()

    with col2:
        start_date = st.date_input(
            "Ngày bắt đầu",
            value=date(2020, 1, 1),
            max_value=date.today()
        )

    with col3:
        end_date = st.date_input(
            "Ngày kết thúc",
            value=date.today(),
            min_value=date(1900, 1, 1),
            max_value=date.today()
        )

    submitted = st.form_submit_button(
        "📊 Vẽ đồ thị",
        use_container_width=True
    )

# ==========================================
# 3. XỬ LÝ DỮ LIỆU VÀ VẼ BIỂU ĐỒ
# ==========================================
if submitted:

    if not ticker:
        st.error("Vui lòng nhập mã cổ phiếu.")

    elif start_date > end_date:
        st.error("Ngày bắt đầu phải nhỏ hơn hoặc bằng ngày kết thúc.")

    else:
        try:
            with st.spinner("Đang tải dữ liệu giá cổ phiếu..."):

                # yfinance sử dụng end_date theo kiểu
                # không bao gồm ngày kết thúc.
                # Cộng thêm 1 ngày để lấy cả ngày người dùng chọn.
                download_end = end_date + timedelta(days=1)

                data = yf.download(
                    ticker,
                    start=start_date.isoformat(),
                    end=download_end.isoformat(),
                    auto_adjust=False,
                    progress=False,
                    threads=False
                )

            if data.empty:
                st.error(
                    f"Không tìm thấy dữ liệu cho mã {ticker} "
                    "trong khoảng thời gian đã chọn. "
                    "Vui lòng kiểm tra mã cổ phiếu hoặc ngày nhập."
                )

            else:
                # ==========================================
                # 4. CHUẨN HÓA DỮ LIỆU
                # ==========================================
                # Một số phiên bản yfinance trả về MultiIndex,
                # kể cả khi chỉ tải một mã cổ phiếu.
                if isinstance(data.columns, pd.MultiIndex):
                    close_data = data.xs(
                        "Close",
                        axis=1,
                        level=0
                    )
                    close_data = close_data.iloc[:, 0]
                else:
                    close_data = data["Close"]

                if isinstance(close_data, pd.DataFrame):
                    close_data = close_data.iloc[:, 0]

                closing_prices = pd.to_numeric(
                    close_data,
                    errors="coerce"
                ).dropna()

                closing_prices = closing_prices.sort_index()

                if closing_prices.empty:
                    st.error("Không có dữ liệu giá đóng cửa hợp lệ.")
                    st.stop()

                # ==========================================
                # 5. LẤY GIÁ ĐÓNG CỬA GẦN NHẤT
                # ==========================================
                latest_price = float(closing_prices.iloc[-1])
                latest_date = pd.Timestamp(
                    closing_prices.index[-1]
                )

                # Tính thay đổi so với phiên giao dịch trước
                if len(closing_prices) >= 2:
                    previous_price = float(closing_prices.iloc[-2])
                    price_change = latest_price - previous_price

                    if previous_price != 0:
                        change_percent = (
                            price_change / previous_price
                        ) * 100
                    else:
                        change_percent = None
                else:
                    previous_price = None
                    price_change = None
                    change_percent = None

                # ==========================================
                # 6. HIỂN THỊ THÔNG TIN GIÁ GẦN NHẤT
                # ==========================================
                st.subheader(f"Thông tin giá cổ phiếu {ticker}")

                st.caption(
                    f"Khoảng thời gian: "
                    f"{start_date.strftime('%d/%m/%Y')} – "
                    f"{end_date.strftime('%d/%m/%Y')}"
                )

                metric1, metric2, metric3 = st.columns(3)

                metric1.metric(
                    label="Giá đóng cửa gần nhất",
                    value=f"{latest_price:,.2f}",
                    help=(
                        "Đơn vị phụ thuộc vào thị trường "
                        "và loại chứng khoán."
                    )
                )

                metric2.metric(
                    label="Ngày giao dịch gần nhất",
                    value=latest_date.strftime("%d/%m/%Y")
                )

                if price_change is not None:
                    delta_text = (
                        f"{change_percent:+.2f}%"
                        if change_percent is not None
                        else None
                    )

                    metric3.metric(
                        label="Thay đổi so với phiên trước",
                        value=f"{price_change:+,.2f}",
                        delta=delta_text
                    )
                else:
                    metric3.metric(
                        label="Thay đổi so với phiên trước",
                        value="Chưa có dữ liệu"
                    )

                st.info(
                    "Giá gần nhất là giá đóng cửa của phiên giao dịch "
                    "cuối cùng có dữ liệu trong khoảng thời gian đã chọn, "
                    "không nhất thiết là giá đang giao dịch trực tiếp."
                )

                # ==========================================
                # 7. VẼ BIỂU ĐỒ GIÁ ĐÓNG CỬA
                # ==========================================
                sns.set_theme(style="whitegrid")

                fig, ax = plt.subplots(figsize=(12, 6))

                ax.plot(
                    closing_prices.index,
                    closing_prices.values,
                    color="limegreen",
                    linewidth=2.0,
                    label=f"Giá đóng cửa {ticker}"
                )

                # Đánh dấu điểm giá đóng cửa gần nhất
                ax.scatter(
                    closing_prices.index[-1],
                    latest_price,
                    color="red",
                    s=60,
                    zorder=5,
                    label="Giá gần nhất"
                )

                ax.annotate(
                    f"{latest_price:,.2f}",
                    xy=(
                        closing_prices.index[-1],
                        latest_price
                    ),
                    xytext=(8, 8),
                    textcoords="offset points",
                    fontsize=10,
                    color="red",
                    fontweight="bold"
                )

                ax.set_title(
                    f"Đồ thị giá cổ phiếu {ticker}",
                    fontsize=15,
                    fontweight="bold",
                    pad=15
                )

                ax.set_xlabel("Thời gian", fontsize=12)
                ax.set_ylabel(
                    "Giá đóng cửa",
                    fontsize=12
                )

                ax.legend(loc="upper left")
                ax.grid(True, linestyle="--", alpha=0.5)

                fig.autofmt_xdate()
                fig.tight_layout()

                st.subheader("Biểu đồ giá đóng cửa")
                st.pyplot(fig, use_container_width=True)

                plt.close(fig)

                # ==========================================
                # 8. HIỂN THỊ BẢNG DỮ LIỆU
                # ==========================================
                st.subheader("Bảng dữ liệu giá cổ phiếu")

                price_table = closing_prices.rename(
                    "Giá đóng cửa"
                ).to_frame()

                price_table.index.name = "Ngày giao dịch"
                price_table = price_table.sort_index(
                    ascending=False
                )

                st.dataframe(
                    price_table.style.format({
                        "Giá đóng cửa": "{:,.2f}"
                    }),
                    use_container_width=True
                )

                # ==========================================
                # 9. TẢI DỮ LIỆU VỀ MÁY
                # ==========================================
                csv_data = price_table.to_csv().encode("utf-8-sig")

                st.download_button(
                    label="⬇️ Tải dữ liệu giá xuống CSV",
                    data=csv_data,
                    file_name=f"{ticker}_gia_co_phieu.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(
                "Đã xảy ra lỗi khi tải hoặc xử lý dữ liệu. "
                "Vui lòng kiểm tra kết nối Internet, mã cổ phiếu "
                "và thử lại."
            )
            st.caption(f"Chi tiết lỗi: {e}")
2. File requirements.txt
Tạo file requirements.txt cùng thư mục với app.py:

text

streamlit>=1.40.0
yfinance>=0.2.50
pandas>=2.0.0
matplotlib>=3.8.0
seaborn>=0.13.0
3. Cấu trúc thư mục

text

stock_app/
├── app.py
└── requirements.txt
