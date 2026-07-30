def encode(s: str) -> str:
    res = []
    for c in s:
        if c == '\\':
            res.append('\\\\')
        elif c == '\n':
            res.append('\\n')
        elif c == '+':
            res.append('++')
        elif c == ' ':
            res.append('+')
        else:
            res.append(c)
    return "".join(res)

def decode(s: str) -> str:
    res = []
    i = 0
    while i < len(s):
        if s[i] == '\\':
            if i + 1 < len(s):
                if s[i+1] == '\\':
                    res.append('\\')
                    i += 2
                elif s[i+1] == 'n':
                    res.append('\n')
                    i += 2
                else:
                    res.append(s[i])
                    i += 1
            else:
                res.append(s[i])
                i += 1
        elif s[i] == '+':
            if i + 1 < len(s) and s[i+1] == '+':
                res.append('+')
                i += 2
            else:
                res.append(' ')
                i += 1
        else:
            res.append(s[i])
            i += 1
    return "".join(res)
