import re


def normalize_cpf(cpf: str) -> str:
    return re.sub(r"\D", "", cpf)


def is_valid_cpf(cpf: str) -> bool:
    digits = normalize_cpf(cpf)

    if len(digits) != 11:
        if len(digits) == 10:
            digits = "0" + digits
        else:
            return False
    if digits == digits[0] * 11:
        return False

    def calc_digit(base: str) -> int:
        weight = sum(int(d) * (len(base) + 1 - i) for i, d in enumerate(base))
        rest = weight % 11
        return 0 if rest < 2 else 11 - rest

    d1 = calc_digit(digits[:9])
    d2 = calc_digit(digits[:10])
    return int(digits[9]) == d1 and int(digits[10]) == d2


def format_cpf(cpf: str) -> str:
    d = normalize_cpf(cpf)
    if len(d) == 10:
        d = "0" + d
    if len(d) != 11:
        return cpf
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
