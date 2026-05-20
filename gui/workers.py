"""Arka plan iş parçacığı — ağır PDF işlemleri UI'ı dondurmaz."""

from __future__ import annotations

from typing import Any, Callable, Optional

from PyQt6.QtCore import QThread, pyqtSignal


ProgressCallback = Callable[[int], None]


class PdfWorker(QThread):
    """
    Evrensel arka plan iş parçacığı.

    Modül fonksiyonları bu sınıfa parametre olarak verilir; işlem `run()`
    içinde çalışır ve ilerleme / sonuç / hata sinyalleri UI'a iletilir.

    Kullanım örneği (ileride):
        worker = PdfWorker(birlestir_pdf, dosya_a, dosya_b)
        worker.progress.connect(ilerleme_cubugu.setValue)
        worker.finished.connect(_islem_tamam)
        worker.error.connect(_hata_goster)
        worker.start()
    """

    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def _ilerleme_gonder(self, yuzde: int) -> None:
        self.progress.emit(max(0, min(100, int(yuzde))))

    def _mesaj_gonder(self, metin: str) -> None:
        self.message.emit(metin)

    def run(self) -> None:
        try:
            kwargs = dict(self._kwargs)
            kwargs.setdefault("progress_callback", self._ilerleme_gonder)
            kwargs.setdefault("message_callback", self._mesaj_gonder)
            sonuc = self._func(*self._args, **kwargs)
            self.finished.emit(sonuc)
        except Exception as exc:  # noqa: BLE001 — UI'ya iletilir
            self.error.emit(str(exc))


class WorkerController:
    """Aktif worker'ı yönetir; yeni işlem başlamadan önce öncekini durdurur."""

    def __init__(self) -> None:
        self._aktif: Optional[PdfWorker] = None

    @property
    def calisiyor(self) -> bool:
        return self._aktif is not None and self._aktif.isRunning()

    def baslat(self, worker: PdfWorker) -> PdfWorker:
        if self.calisiyor and self._aktif is not None:
            self._aktif.requestInterruption()
            self._aktif.wait(3000)
        self._aktif = worker
        worker.finished.connect(self._temizle)
        worker.error.connect(self._temizle)
        worker.start()
        return worker

    def _temizle(self, *_args: Any) -> None:
        if self._aktif is not None:
            self._aktif.deleteLater()
            self._aktif = None
