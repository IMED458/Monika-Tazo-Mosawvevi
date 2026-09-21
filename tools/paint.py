"""Photo -> soft gouache/watercolour plate, matching the hand-painted venue
artwork in the reference invitation: broad flat colour, a soft ink line only
where a real edge is, warm paper tone. Tuned for busy subjects (lattice work)
where naive posterising just produces colour speckle."""
import sys
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageChops

def painterly(src, out, size=(1100,1100), centering=(0.5,0.45), soften=1.0):
    im = Image.open(src).convert("RGB")
    im = ImageOps.fit(im, size, Image.LANCZOS, centering=centering)

    # Work large-ish, smooth hard, then quantise: median-cut over an already
    # smoothed image gives flat paint fields instead of per-pixel speckle.
    soft = im.filter(ImageFilter.GaussianBlur(2.2*soften))
    soft = soft.filter(ImageFilter.MedianFilter(9 if soften>=1 else 7))
    soft = soft.filter(ImageFilter.GaussianBlur(2.6*soften))

    flat = soft.quantize(colors=20, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    flat = flat.filter(ImageFilter.GaussianBlur(1.4*soften))
    # A little of the real photo back in, so it reads as a painting of the
    # place and not a vector poster.
    art = Image.blend(flat, soft, 0.30)

    # Ink line: only strong edges survive the threshold, so the ferris-wheel
    # lattice contributes a suggestion of structure rather than a wire mesh.
    g = im.convert("L").filter(ImageFilter.GaussianBlur(1.8))
    e = g.filter(ImageFilter.FIND_EDGES)
    e = ImageOps.autocontrast(e)
    e = e.point(lambda v: 255 if v < 62 else 255 - int((v-62)*0.55))
    e = e.filter(ImageFilter.GaussianBlur(0.9))
    art = ImageChops.multiply(art, e.convert("RGB"))

    # Warm wash + gentle lift, the cream-paper key of the invitation.
    art = ImageEnhance.Color(art).enhance(0.9)
    art = ImageEnhance.Brightness(art).enhance(1.05)
    art = ImageEnhance.Contrast(art).enhance(1.04)
    r, gg, b = art.split()
    r  = r.point(lambda v: min(255, int(v*1.03 + 9)))
    gg = gg.point(lambda v: min(255, int(v*1.0  + 5)))
    b  = b.point(lambda v: min(255, int(v*0.94 + 2)))
    art = Image.merge("RGB", (r, gg, b))

    # Faint paper tooth (very light — heavy grain fought the flat fields).
    tooth = Image.effect_noise(size, 9).convert("L").filter(ImageFilter.GaussianBlur(0.9))
    art = Image.blend(art, ImageChops.overlay(art, tooth.convert("RGB")), 0.08)

    # Bring the brush strokes back to a crisp edge after all that blurring.
    art = art.filter(ImageFilter.UnsharpMask(radius=3, percent=int(70/soften), threshold=3))
    art.save(out, "JPEG", quality=90, optimize=True, progressive=True)
    print(out, art.size)

if __name__ == "__main__":
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 1100
    h = int(sys.argv[4]) if len(sys.argv) > 4 else 1100
    cy = float(sys.argv[5]) if len(sys.argv) > 5 else 0.45
    sf = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
    painterly(sys.argv[1], sys.argv[2], (w, h), (0.5, cy), sf)
