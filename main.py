import requests
from time import sleep
from re import search

# ==================== تنظیمات ====================
channel = "Reaction2026"  # نام کانال بدون @
post = 120  # شماره پست
views_count = 100  # تعداد ویو
delay = 3  # تأخیر بین ویوها (ثانیه)

# ==================== تابع ویو زدن ====================
def send_view():
    session = requests.session()
    
    try:
        # دریافت توکن
        response = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={
                'referer': f'https://t.me/{channel}/{post}',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        token = search('data-view="([^"]+)', response.text)
        if not token:
            print(" [✗] توکن دریافت نشد")
            return False
        
        # ارسال ویو
        view_response = session.get(
            'https://t.me/v/',
            params={'views': token.group(1)},
            headers={
                'referer': f'https://t.me/{channel}/{post}?embed=1&mode=tme',
                'x-requested-with': 'XMLHttpRequest'
            }
        )
        
        if view_response.status_code == 200 and view_response.text == 'true':
            print(f" [✓] ویو شماره {i+1} ثبت شد")
            return True
        else:
            print(f" [✗] ویو شماره {i+1} ثبت نشد")
            return False
            
    except Exception as e:
        print(f" [✗] خطا: {e}")
        return False

# ==================== اجرا ====================
print(f"\n🚀 شروع ویو زدن برای @{channel}/{post}")
print(f"📊 تعداد ویو: {views_count}\n")

success = 0
for i in range(views_count):
    if send_view():
        success += 1
    sleep(delay)

print(f"\n📈 نتیجه نهایی:")
print(f"   ✅ موفق: {success}")
print(f"   ❌ ناموفق: {views_count - success}")
