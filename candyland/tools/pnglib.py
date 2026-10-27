"""PNG / TGA writers used by the Candyland pack builder (stdlib only)."""
import struct
import zlib


def png_write(path, width, height, rgba):
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw += rgba[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    blob = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(blob)


def tga_write(path, width, height, rgba):
    """Uncompressed 32-bit BGRA TGA, top-left origin.

    Bedrock's vanilla leaves / grass-side / plant textures are TGAs; writing
    the same extension avoids relying on the client's extension fallback.
    """
    header = struct.pack("<BBBHHBHHHHBB",
                         0, 0, 2,          # id len, cmap, truecolour
                         0, 0, 0,          # cmap spec
                         0, 0,             # origin
                         width, height,
                         32, 0x28)         # 8 alpha bits, top-left origin
    out = bytearray(header)
    for i in range(0, len(rgba), 4):
        out += bytes((rgba[i + 2], rgba[i + 1], rgba[i], rgba[i + 3]))
    with open(path, "wb") as fh:
        fh.write(out)


def read_png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a png: " + path)
    return struct.unpack(">II", head[16:24])


# ------------------------------------------------------------------ reading

def read_png(path):
    """Decode a non-interlaced 8-bit PNG to (w, h, bytearray RGBA)."""
    import zlib
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a png: " + path)
    pos = 8
    idat = bytearray()
    palette = None
    trns = None
    w = h = depth = ctype = None
    interlace = 0
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if tag == b"IHDR":
            w, h, depth, ctype, comp, filt, interlace = struct.unpack(
                ">IIBBBBB", chunk)
        elif tag == b"PLTE":
            palette = chunk
        elif tag == b"tRNS":
            trns = chunk
        elif tag == b"IDAT":
            idat += chunk
        elif tag == b"IEND":
            break
    if depth != 8 or interlace:
        raise ValueError("unsupported png (depth=%s interlace=%s): %s"
                         % (depth, interlace, path))
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(bytes(idat))
    stride = w * channels
    out = bytearray(w * h * 4)
    prev = bytearray(stride)
    src = 0
    for y in range(h):
        f = raw[src]
        src += 1
        line = bytearray(raw[src:src + stride])
        src += stride
        if f == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        prev = line
        row = y * w * 4
        if ctype == 6:
            out[row:row + w * 4] = line
        elif ctype == 2:
            for x in range(w):
                out[row + x * 4:row + x * 4 + 3] = line[x * 3:x * 3 + 3]
                out[row + x * 4 + 3] = 255
        elif ctype == 0:
            for x in range(w):
                g = line[x]
                out[row + x * 4:row + x * 4 + 3] = bytes((g, g, g))
                out[row + x * 4 + 3] = 255
        elif ctype == 4:
            for x in range(w):
                g, a = line[x * 2], line[x * 2 + 1]
                out[row + x * 4:row + x * 4 + 3] = bytes((g, g, g))
                out[row + x * 4 + 3] = a
        elif ctype == 3:
            for x in range(w):
                idx = line[x]
                out[row + x * 4:row + x * 4 + 3] = palette[idx * 3:idx * 3 + 3]
                out[row + x * 4 + 3] = (trns[idx] if trns and idx < len(trns)
                                        else 255)
    return w, h, out


def read_tga(path):
    """Decode uncompressed or RLE 24/32-bit TGA to (w, h, RGBA)."""
    with open(path, "rb") as fh:
        d = fh.read()
    idlen, cmap, typ = d[0], d[1], d[2]
    w, h = struct.unpack("<HH", d[12:16])
    bpp = d[16]
    desc = d[17]
    pos = 18 + idlen
    if cmap:
        pos += d[7] * d[5] // 8 if False else 0
    out = bytearray(w * h * 4)
    nbytes = bpp // 8
    if typ == 2:
        px = d[pos:pos + w * h * nbytes]
        for i in range(w * h):
            b = px[i * nbytes:i * nbytes + nbytes]
            out[i * 4:i * 4 + 3] = bytes((b[2], b[1], b[0]))
            out[i * 4 + 3] = b[3] if nbytes == 4 else 255
    elif typ == 10:
        i = 0
        o = 0
        total = w * h
        while i < total:
            head = d[pos]
            pos += 1
            count = (head & 0x7F) + 1
            if head & 0x80:
                b = d[pos:pos + nbytes]
                pos += nbytes
                for _ in range(count):
                    out[o * 4:o * 4 + 3] = bytes((b[2], b[1], b[0]))
                    out[o * 4 + 3] = b[3] if nbytes == 4 else 255
                    o += 1
            else:
                for _ in range(count):
                    b = d[pos:pos + nbytes]
                    pos += nbytes
                    out[o * 4:o * 4 + 3] = bytes((b[2], b[1], b[0]))
                    out[o * 4 + 3] = b[3] if nbytes == 4 else 255
                    o += 1
            i += count
    else:
        raise ValueError("unsupported tga type %d: %s" % (typ, path))
    if not (desc & 0x20):
        flipped = bytearray(len(out))
        stride = w * 4
        for y in range(h):
            flipped[y * stride:(y + 1) * stride] = out[(h - 1 - y) * stride:
                                                       (h - y) * stride]
        out = flipped
    return w, h, out


def read_image(path):
    with open(path, "rb") as fh:
        head = fh.read(8)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return read_png(path)
    return read_tga(path)
