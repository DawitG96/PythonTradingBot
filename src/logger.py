import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

class IterLoggerWithSave:
    def __init__(self, items:list, stream=sys.stdout, progress_file:str=None):
        self.stream = stream
        self.progress_file = progress_file
        if not self.load():
            self.items = items
            self.completed = 0
            self.avg_time = 0
        self.total = len(self.items)

    def print_with_time(self, string:str):
        now = datetime.now(timezone.utc)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{now_str}] - {string}", file=self.stream)

    def save(self):
        if self.progress_file is None:
            return
        with open(self.progress_file, 'w') as f:
            json.dump({'items': self.items, 'completed': self.completed, 'avg_time': self.avg_time}, f)

    def load(self):
        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                self.completed = data.get('completed')
                self.items = data.get('items')
                self.avg_time = data.get('avg_time')
            self.print_with_time(f"⚠️ Riprendo da {self.completed + 1}/{len(self.items)} elementi...")
            return True
        except Exception:
            return False

    def progress(self, start_time:float):
        delta = time.time() - start_time
        if self.completed > 0:
            total_time = self.avg_time * (self.completed - 1)
            self.avg_time = (total_time + delta) / self.completed

        percent = self.completed / self.total
        remaining = self.avg_time * (self.total - self.completed)
        remaining_str = str(timedelta(seconds=remaining))[:-3]

        self.completed += 1
        return f"{remaining_str} ({percent: 6.2%}) inizio {self.completed}/{self.total}"

    def __iter__(self):
        start_time = time.time()
        for i, item in enumerate(self.items[self.completed:]):
            prog_string = self.progress(start_time)
            self.print_with_time(f"🕒 {prog_string} {item}")

            start_time = time.time()
            yield item
            self.save()
        self.print_with_time(f"✅ Completato {self.completed} elementi!")
        os.remove(self.progress_file)

