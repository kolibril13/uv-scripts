# /// script
# dependencies = [
#   "librosa",
#   "noisereduce",
#   "soundfile",
#   "numpy",
# ]
# ///

from pathlib import Path
import numpy as np
import librosa
import soundfile as sf
import noisereduce as nr

TAPS_DIR = Path.home() / "Downloads" /


def denoise_file(path: Path):
    print(f"Processing: {path.name}")

    # Load wav (preserve original samplerate)
    y, sr = librosa.load(path, sr=None, mono=True)

    # Use last 0.5s as noise profile
    noise_sample_len = int(sr * 0.5)
    noise_profile = y[-noise_sample_len:]

    # Spectral noise reduction
    y_denoised = nr.reduce_noise(
        y=y,
        sr=sr,
        y_noise=noise_profile,
        prop_decrease=1.0,
        stationary=True,
    )

    out_path = path.with_name(path.stem + "_denoised.wav")
    sf.write(out_path, y_denoised, sr)

    print(f" → wrote {out_path.name}")


def main():
    wav_files = sorted(TAPS_DIR.glob("*.wav"))

    if not wav_files:
        print("No wav files found in:", TAPS_DIR)
        return

    for wav in wav_files:
        try:
            denoise_file(wav)
        except Exception as e:
            print(f"Failed on {wav.name}: {e}")


if __name__ == "__main__":
    main()
