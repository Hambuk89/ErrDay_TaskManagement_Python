
from PIL import Image, ImageDraw

SIZE = 512
image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Blue Rounded Rectangle Background
draw.rounded_rectangle(
    (18, 18, 494, 494),
    radius=100,
    fill=(39, 116, 245, 255)
)

# White Calendar
draw.rounded_rectangle(
    (90, 112, 422, 420),
    radius=44,
    fill=(248, 251, 255, 255)
)

# Calendar Header
draw.rounded_rectangle(
    (90, 112, 422, 208),
    radius=44,
    fill=(113, 181, 255, 255)
)
draw.rectangle(
    (90, 166, 422, 208),
    fill=(113, 181, 255, 255)
)

# Calendar Rings
for x in (172, 340):
    draw.rounded_rectangle(
        (x - 17, 76, x + 17, 155),
        radius=17,
        fill="white"
    )

# date boxes
for x in (143, 211, 279):
    for y in (240, 294):
        draw.rounded_rectangle(
            (x, y, x + 38, y + 38),
            radius=10,
            fill=(193, 209, 230, 255)
        )

# check mark background
draw.ellipse(
    (260, 280, 420, 440),
    fill="white"
)
draw.ellipse(
    (271, 291, 409, 429),
    fill=(21, 96, 230, 255)
)

# check mark
points = [(305, 359), (335, 387), (380, 330)]
draw.line(points, fill="white", width=18, joint="curve")

for x, y in points:
    r = 9
    draw.ellipse(
        (x-r, y-r, x+r, y+r),
        fill="white"
    )

# Icon save
image.save("errday_icon.png")
image.save(
    "errday_icon.ico",
    format="ICO",
    sizes=[
        (16, 16), (24, 24), (32, 32),
        (48, 48), (64, 64), (128, 128),
        (256, 256)
    ]
)

print("ErrDay 아이콘 생성 완료!")
