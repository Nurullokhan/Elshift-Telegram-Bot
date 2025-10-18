from PIL import Image

# 🔹 Logotipni yuklash
logo = Image.open("elshift_logo_640x360.png").convert("RGBA")

frames = []

# 🔹 1-qism: kichikdan kattalashish (40% → 100%)
for scale in range(40, 101, 5):
    new_size = (logo.width * scale // 100, logo.height * scale // 100)
    
    # Qora fon (RGBA = qora)
    frame = Image.new("RGBA", logo.size, (0, 0, 0, 255))
    
    # Logotipni masshtablash
    resized = logo.resize(new_size, Image.LANCZOS)
    
    # Markazga joylashtirish
    position = ((logo.width - new_size[0]) // 2, (logo.height - new_size[1]) // 2)
    frame.paste(resized, position, resized)
    
    frames.append(frame)

# 🔹 2-qism: kattadan kichrayish (100% → 40%)
for scale in range(95, 40, -5):
    new_size = (logo.width * scale // 100, logo.height * scale // 100)
    frame = Image.new("RGBA", logo.size, (0, 0, 0, 255))
    resized = logo.resize(new_size, Image.LANCZOS)
    position = ((logo.width - new_size[0]) // 2, (logo.height - new_size[1]) // 2)
    frame.paste(resized, position, resized)
    frames.append(frame)

# 🔹 GIF sifatida saqlash
frames[0].save(
    "logo_animation_40_100.gif",
    save_all=True,
    append_images=frames[1:],
    duration=80,  # har freym uchun vaqt (ms)
    loop=0,       # 0 = cheksiz takrorlanadi
    disposal=2
)

print("✅ Tayyor! Fayl: logo_animation_40_100.gif")
