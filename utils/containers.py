# containers.py

import numpy as np

class OSRSObject:
    times = {
        '1 month': 'day30',
        '1m' : 'day30',
        '30 days': 'day30',
        '30d': 'day30',
        '3 months': 'day90',
        '3m': 'day90',
        '90 days': 'day90',
        '90d': 'day90',
        '6 months': 'day180',
        '6m': 'day180',
        '180 days': 'day180',
        '180d': 'day180'
    }
    def __init__(self, data):
        data = data['item']
        for k, v in data.items():
            setattr(self, k, v)

    def __repr__(self): return f"<class OSRSObject; name=\"{self.name}\", current price={self.current['price']} gp>"

    def show(self, time: str):
        if time in self.times.keys():
            print(getattr(self, self.times[time]))

    @property
    def print(self):
        out = f"Name: {self.name}\n"
        out += f"ID: {self.id}\n"
        out += f"Description: {self.description}\n"
        out += f"Current price: {self.current['price']}\n"
        out += f"Current trend: {self.current['trend']}\n"
        return out


class DieEval:
    value = 0
    average = 0
    ops = {'-': lambda l, r: l - r, '+': lambda l, r: l + r}

    def __init__(self, num, die, op, mod):
        self.num = int(num)
        self.die = int(die)
        self.op = op
        self.mod = int(mod)
        self.eval()

    def eval(self):
        self.rolls = [np.random.randint(1, self.die) for _ in range(self.num)]
        self.average = sum(self.rolls) / len(self.rolls)
        self.total = self.ops[self.op](sum(self.rolls), self.mod)

    @classmethod
    def generate(cls, **kwargs):
        """Makes a random die object, but you can pass each param as a kwarg if you want"""
        num_min = kwargs.pop('num_min', None) or 1
        num_max = kwargs.pop('num_max', None) or 20
        num_min, num_max = min(num_min, num_max), max(num_min, num_max) #sanity checks

        size_min = kwargs.pop('size_min', None) or 2
        size_max = kwargs.pop('size_max', None) or 20
        size_min, size_max = min(size_min, size_max), max(size_min, size_max)

        op = kwargs.pop('op', None) or np.random.choice(['+', '-'])

        mod_min = kwargs.pop('mod_min', None) or 0
        mod_max = kwargs.pop('mod_max', None) or 10
        mod_min, mod_max = min(mod_min, mod_max), max(mod_min, mod_max)

        num = np.random.randint(num_min, num_max)
        size = np.random.choice(np.arange(size_min, size_max, 2))
        mod = np.random.randint(mod_min, mod_max)

        return cls(num, size, op, mod)

    def __str__(self):
        if self.mod != 0:
            return f"{self.num}d{self.die}{self.op}{self.mod} => {self.total}"
        return f"{self.num}d{self.die} => {self.total}"

    def __repr__(self):
        num = self.num
        die = self.die
        op = self.op
        mod = self.mod
        if mod != 0:
            return f"<class DieEval; total={self.total}, {num}d{die}{op}{mod}>"
        return f"<class DieEval; total={self.total}, {num}d{die}>"

    def __int__(self): return self.total

    def __add__(self, other):
        return self.total + int(other)

    def __sub__(self, other):
        return self.total - int(other)

    def print(self):
        out = f"{self} -> {self.total}\nRolls: "
        out += ', '.join(map(str, sorted(self.rolls, reverse=True)))
        out += f"\nAverage roll: {self.average:.2f}"
        return out