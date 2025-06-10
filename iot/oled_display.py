import time
import board
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

# --- OLED 相關設定 ---
# 使用 I2C：
i2c = board.I2C()
try:
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C) # 檢查你的 OLED 位址，可能是 0x3D
except RuntimeError as e:
    print(f"OLED 初始化失敗：{e}. 請檢查 I2C 連線和位址。")
    exit()

# --- 字型路徑設定 ---
font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc' # 預設中文字型路徑

def display_text_oled(text, x, y, font_size=16, font_path=font_path):
    """在 OLED 上顯示文字。"""
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"字型檔案 {font_path} 未找到，使用預設字型。")
        font = ImageFont.load_default()
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    draw.text((x, y), text, 1, font=font)
    oled.image(image)
    oled.show()

def scroll_text_oled(text, y, font_size=16, scroll_speed=0.1, font_path=font_path):
    """在 OLED 的指定列上滾動顯示文字。"""
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"字型檔案 {font_path} 未找到，使用預設字型。")
        font = ImageFont.load_default()
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    text_width = int(draw.textlength(text, font=font))
    for i in range(oled.width + text_width):
        image = Image.new('1', (oled.width, oled.height))
        draw = ImageDraw.Draw(image)
        x = oled.width - i
        if x < -text_width:
            break
        draw.text((x, y), text, 1, font=font)
        oled.image(image)
        oled.show()
        time.sleep(scroll_speed)

def display_image_oled(image_path):
    """在 OLED 上顯示圖片。"""
    try:
        image = Image.open(image_path).convert('1').resize((oled.width, oled.height), Image.Resampling.LANCZOS)
        oled.image(image)
        oled.show()
    except FileNotFoundError:
        print(f"圖片檔案 {image_path} 未找到。")

def clear_oled():
    """清除 OLED 螢幕。"""
    oled.fill(0)
    oled.show()

def main():
    try:
        print("OLED 上固定文字與下方跑馬燈...")
        clear_oled()

        # 固定顯示在上方的文字
        fixed_text_line1 = "藍線 1 號"
        display_text_oled(fixed_text_line1, 0, 10, font_size=16)

        while True:
            # 在下方滾動的文字
            scrolling_text_line2 = "末班已過 請改搭其他交通工具"
            scroll_text_oled(scrolling_text_line2, 30, font_size=16, scroll_speed=0.08)
            time.sleep(0.5) # 每次滾動結束後稍微停頓一下

    except KeyboardInterrupt:
        print("程式終止。")
    finally:
        clear_oled()
        

if __name__ == "__main__":
    main()


