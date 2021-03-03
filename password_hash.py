def safe_add(n, t):
    i = (n & 65535) + (t & 65535)
    r = (n >> 16) + (t >> 16) + (i >> 16)
    return move_left(r, 16) | i & 65535


def move_left(n, t):
    n = bin(n)

    positive1 = n[0] != '-'
    n = str(n)[3:] if n[0] == '-' else str(n)[2:]
    n = n.zfill(32)

    ###########
    n1 = ['0' if n[i] == '1' else '1' for i in range(len(n))]
    done = False
    for i in range(len(n1) - 1, -1, -1):
        if n1[i] == '0':
            n1[i] = '1'
            done = True
            break
        n1[i] = '0'
    n1 = ''.join(n1)
    if not done:
        n1 = '1' + n1
    ############

    n1 = n1[t:] + '0' * t
    if n1[0] == '1':
        n1 = n[t:] + '0' * t
        positive3 = True
    else:
        positive3 = False

    positive2 = True if n1[0] == '1' else False
    n1 = str(int(n1, 2))
    if positive2 or (positive1 + positive3 == 1):
        n1 = '-' + n1
    return int(n1)


def move(n, t):
    n = bin(n)

    positive = n[0] != '-'
    n = str(n)[3:] if n[0] == '-' else str(n)[2:]
    n = n.zfill(32)

    if not positive:
        n = ['0' if n[i] == '1' else '1' for i in range(len(n))]
        done = False
        for i in range(len(n) - 1, -1, -1):
            if n[i] == '0':
                n[i] = '1'
                done = True
                break
            n[i] = '0'
        n = ''.join(n)
        if not done:
            n = '1' + n

    n = '0' * t + n[:-t]
    return int(n, 2)


def rol(n, t):
    return move_left(n, t) | move(n, 32 - t)


def cmn(n, t, i, r, u, f):
    return safe_add(rol(safe_add(safe_add(t, n), safe_add(r, f)), u), i)


def ff(n, t, i, r, u, f, e):
    return cmn(t & i | ~t & r, n, t, u, f, e)


def gg(n, t, i, r, u, f, e):
    return cmn(t & r | i & ~r, n, t, u, f, e)


def hh(n, t, i, r, u, f, e):
    return cmn(t ^ i ^ r, n, t, u, f, e)


def ii(n, t, i, r, u, f, e):
    return cmn(i ^ (t | ~r), n, t, u, f, e)


def coreMD5(n):
    t = 1732584193
    r = -271733879
    u = -1732584194
    f = 271733878
    for i in range(0, len(n), 16):
        e = t
        o = r
        s = u
        h = f
        t = ff(t, r, u, f, n[i + 0], 7, -680876936)
        f = ff(f, t, r, u, n[i + 1], 12, -389564586)
        u = ff(u, f, t, r, n[i + 2], 17, 606105819)
        r = ff(r, u, f, t, n[i + 3], 22, -1044525330)
        t = ff(t, r, u, f, n[i + 4], 7, -176418897)
        f = ff(f, t, r, u, n[i + 5], 12, 1200080426)
        u = ff(u, f, t, r, n[i + 6], 17, -1473231341)
        r = ff(r, u, f, t, n[i + 7], 22, -45705983)
        t = ff(t, r, u, f, n[i + 8], 7, 1770035416)
        f = ff(f, t, r, u, n[i + 9], 12, -1958414417)
        u = ff(u, f, t, r, n[i + 10], 17, -42063)
        r = ff(r, u, f, t, n[i + 11], 22, -1990404162)
        t = ff(t, r, u, f, n[i + 12], 7, 1804603682)
        f = ff(f, t, r, u, n[i + 13], 12, -40341101)
        u = ff(u, f, t, r, n[i + 14], 17, -1502002290)
        r = ff(r, u, f, t, n[i + 15], 22, 1236535329)
        t = gg(t, r, u, f, n[i + 1], 5, -165796510)
        f = gg(f, t, r, u, n[i + 6], 9, -1069501632)
        u = gg(u, f, t, r, n[i + 11], 14, 643717713)
        r = gg(r, u, f, t, n[i + 0], 20, -373897302)
        t = gg(t, r, u, f, n[i + 5], 5, -701558691)
        f = gg(f, t, r, u, n[i + 10], 9, 38016083)
        u = gg(u, f, t, r, n[i + 15], 14, -660478335)
        r = gg(r, u, f, t, n[i + 4], 20, -405537848)
        t = gg(t, r, u, f, n[i + 9], 5, 568446438)
        f = gg(f, t, r, u, n[i + 14], 9, -1019803690)
        u = gg(u, f, t, r, n[i + 3], 14, -187363961)
        r = gg(r, u, f, t, n[i + 8], 20, 1163531501)
        t = gg(t, r, u, f, n[i + 13], 5, -1444681467)
        f = gg(f, t, r, u, n[i + 2], 9, -51403784)
        u = gg(u, f, t, r, n[i + 7], 14, 1735328473)
        r = gg(r, u, f, t, n[i + 12], 20, -1926607734)
        t = hh(t, r, u, f, n[i + 5], 4, -378558)
        f = hh(f, t, r, u, n[i + 8], 11, -2022574463)
        u = hh(u, f, t, r, n[i + 11], 16, 1839030562)
        r = hh(r, u, f, t, n[i + 14], 23, -35309556)
        t = hh(t, r, u, f, n[i + 1], 4, -1530992060)
        f = hh(f, t, r, u, n[i + 4], 11, 1272893353)
        u = hh(u, f, t, r, n[i + 7], 16, -155497632)
        r = hh(r, u, f, t, n[i + 10], 23, -1094730640)
        t = hh(t, r, u, f, n[i + 13], 4, 681279174)
        f = hh(f, t, r, u, n[i + 0], 11, -358537222)
        u = hh(u, f, t, r, n[i + 3], 16, -722521979)
        r = hh(r, u, f, t, n[i + 6], 23, 76029189)
        t = hh(t, r, u, f, n[i + 9], 4, -640364487)
        f = hh(f, t, r, u, n[i + 12], 11, -421815835)
        u = hh(u, f, t, r, n[i + 15], 16, 530742520)
        r = hh(r, u, f, t, n[i + 2], 23, -995338651)
        t = ii(t, r, u, f, n[i + 0], 6, -198630844)
        f = ii(f, t, r, u, n[i + 7], 10, 1126891415)
        u = ii(u, f, t, r, n[i + 14], 15, -1416354905)
        r = ii(r, u, f, t, n[i + 5], 21, -57434055)
        t = ii(t, r, u, f, n[i + 12], 6, 1700485571)
        f = ii(f, t, r, u, n[i + 3], 10, -1894986606)
        u = ii(u, f, t, r, n[i + 10], 15, -1051523)
        r = ii(r, u, f, t, n[i + 1], 21, -2054922799)
        t = ii(t, r, u, f, n[i + 8], 6, 1873313359)
        f = ii(f, t, r, u, n[i + 15], 10, -30611744)
        u = ii(u, f, t, r, n[i + 6], 15, -1560198380)
        r = ii(r, u, f, t, n[i + 13], 21, 1309151649)
        t = ii(t, r, u, f, n[i + 4], 6, -145523070)
        f = ii(f, t, r, u, n[i + 11], 10, -1120210379)
        u = ii(u, f, t, r, n[i + 2], 15, 718787259)
        r = ii(r, u, f, t, n[i + 9], 21, -343485551)
        t = safe_add(t, e)
        r = safe_add(r, o)
        u = safe_add(u, s)
        f = safe_add(f, h)
    return (t, r, u, f)


def binl2hex(n):
    i = "0123456789abcdef"
    r = ""
    for t in range(0, len(n) * 4, 1):
        r += i[n[t >> 2] >> t % 4 * 8 + 4 & 15] + i[n[t >> 2] >> t % 4 * 8 & 15]
    return r


def str2binl_(n):
    r = (len(n) + 8 >> 6) + 1
    i = [0] * (r * 16)
    for t in range(0, len(n), 1):
        i[t >> 2] |= (charCodeAt_(n, t) & 255) << t % 4 * 8
    t += 1
    i[t >> 2] |= 128 << t % 4 * 8
    i[r * 16 - 2] = len(n) * 8
    return i


def charCodeAt_(n, t):
    i = ord(n[t])
    return i if i >= 0 and i <= 255 else (i - 848 if i >= 1040 and i <= 1103 else (168 if i == 1025 else (184 if i == 1105 else (185 if i == 8470 else 0))))


def hexMD5_(n):
    return binl2hex(coreMD5(str2binl_(n)))


def get_pw(salt, passwd):
    return hexMD5_(str(salt) + hexMD5_(passwd))
