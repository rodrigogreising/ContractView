"""Replaceable Tesseract CLI extraction adapter."""

from decimal import Decimal
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from ...extraction import ExtractionProviderError, InvalidExtractionResponse, OcrResponse


class TesseractCliAdapter:
    provider = "tesseract-cli"
    model = "tesseract-runtime-eng"

    def extract(self, filename: str, media_type: str, content: bytes) -> OcrResponse:
        with TemporaryDirectory(prefix="contractview-ocr-") as directory:
            root = Path(directory)
            source = root / Path(filename).name
            source.write_bytes(content)
            image = source
            if media_type == "application/pdf":
                image = root / "page-1.png"
                result = subprocess.run(
                    ["pdftoppm", "-f", "1", "-singlefile", "-png", "-r", "200", str(source), str(root / "page-1")],
                    capture_output=True, text=True,
                )
                if result.returncode != 0:
                    raise ExtractionProviderError(result.stderr.strip() or "PDF rendering failed")
            try:
                version_result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, timeout=10)
                text_result = subprocess.run(["tesseract", str(image), "stdout", "-l", "eng+spa", "--psm", "6"], capture_output=True, text=True, timeout=30)
                tsv_result = subprocess.run(["tesseract", str(image), "stdout", "-l", "eng+spa", "--psm", "6", "tsv"], capture_output=True, text=True, timeout=30)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise ExtractionProviderError(f"OCR provider unavailable: {error}") from error
            if text_result.returncode != 0 or tsv_result.returncode != 0:
                raise ExtractionProviderError(text_result.stderr.strip() or tsv_result.stderr.strip() or "OCR failed")
            confidences = []
            for line in tsv_result.stdout.splitlines()[1:]:
                cells = line.split("\t")
                if len(cells) >= 12 and cells[11].strip():
                    try:
                        value = Decimal(cells[10])
                        if value >= 0:
                            confidences.append(value)
                    except Exception:
                        pass
            if not text_result.stdout.strip() or not confidences:
                raise InvalidExtractionResponse("OCR returned no usable text")
            confidence = (sum(confidences, Decimal("0")) / len(confidences) / Decimal("100")).quantize(Decimal("0.0001"))
            runtime_version = version_result.stdout.splitlines()[0].split(maxsplit=1)[1] if version_result.returncode == 0 else "unknown"
            return OcrResponse(self.provider, f"tesseract-{runtime_version}-eng+spa", text_result.stdout, confidence)
