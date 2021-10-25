import nidaqmx
import nidaqmx.system
from nidaqmx.constants import (AcquisitionType, CountDirection, Edge,
                               READ_ALL_AVAILABLE, TaskMode, TriggerType)
from nidaqmx.stream_readers import CounterReader
import numpy as np
from time import time
import matplotlib.pyplot as plt
import pickle
from scipy.io import wavfile
import sounddevice as sd

system = nidaqmx.system.System.local()
device = system.devices[0] if system.devices else None


def turn_off_led():
    with nidaqmx.Task() as tx:
        tx.ao_channels.add_ao_voltage_chan(device.name + "/ao0")
        tx.write(0, True)


def take_measurements(signal: np.ndarray, sampling_rate: float):
    t = signal.size / sampling_rate
    with nidaqmx.Task() as rx, nidaqmx.Task() as tx, nidaqmx.Task() as clock:
        rx.ai_channels.add_ai_current_chan(device.name + "/ai0")
        rx.timing.cfg_samp_clk_timing(sampling_rate, sample_mode=AcquisitionType.CONTINUOUS)
        tx.ao_channels.add_ao_voltage_chan(device.name + "/ao0")
        tx.timing.cfg_samp_clk_timing(sampling_rate, sample_mode=AcquisitionType.CONTINUOUS)
        # clock.di_channels.add_di_chan(device.name+"/port0")
        # clock.timing.cfg_samp_clk_timing(sumpeling_rate, sample_mode=AcquisitionType.CONTINUOUS)
        tx.stop()
        tx.write(signal + 3)
        # vals = [rx.read() for _ in range(100)]
        vals = []
        start_time = time()
        tx.start()
        while time() - start_time < t:
            vals.append(rx.read())
        tx.stop()
        tx.write([0, 0, 0], True)
        tx.stop()
        # print(f"{rx.read()=}")
        # for s in signal+7:
        #     tx.write(s)
    return vals


def distance(x1):
    w = 570
    T = 5
    rate = 10000
    x0 = 20
    dis = x1 - x0
    filename = f"distance/distance{dis}"
    sig = np.sin(w * np.linspace(0, T, T * rate) * 2 * np.pi) / 2
    values = take_measurements(sig, rate)
    plt.plot(values)
    plt.show()
    with open(filename, "wb+") as f:
        pickle.dump({"signal": sig, "received": values, "interval": T, "rate": rate, "time": time(), "distance": dis},
                    f)


def noise():
    w = 570
    T = 5
    rate = 10000
    # x0 = 20
    # dis = x1 - x0
    filename = f"noise_cover_photo_diode.pickle"
    sig = np.sin(w * np.linspace(0, T, T * rate) * 2 * np.pi) / 2
    values = take_measurements(sig, rate)
    plt.plot(values)
    plt.show()
    with open(filename, "wb+") as f:
        pickle.dump({"signal": sig, "received": values, "interval": T, "rate": rate, "time": time()}, f)


def song(filename, output_name="out.wav"):
    sample_rate, data = wavfile.read(filename)
    data = np.array(data[:, 0] / (2 ** 15 - 1))
    sliced_data = data[0:10 * sample_rate]
    values = take_measurements(sliced_data, sample_rate)
    values = np.array(values)
    values -= np.average(values)
    values *= (2**15 - 1)/max(values.max(), -values.min())
    values = values.round().astype("int16")
    print(f"{values.size=}\n{sample_rate=}")
    wavfile.write(output_name, sample_rate, values)


def play_song(filename, chunk_size=1000):
    sample_rate, data = wavfile.read(filename)
    data = np.array(data[:, 0] / (2 ** 15 - 1))
    for chunk in (data[pos:pos+chunk_size] for pos in range(0,data.size,chunk_size)):
        values = take_measurements(chunk, sample_rate)
        values = np.array(values)
        values -= np.average(values)
        values *= (2**15 - 1)/max(values.max(), -values.min())
        values = values.round().astype("int16")
        sd.play(values, sample_rate)



# def read(f, normalized=False):
#     """MP3 to numpy array"""
#     a = pydub.AudioSegment.from_mp3(f)
#     y = np.array(a.get_array_of_samples())
#     if a.channels == 2:
#         y = y.reshape((-1, 2))
#     if normalized:
#         return a.frame_rate, np.float32(y) / 2**15
#     else:
#         return a.frame_rate, y
#
# def write(f, sr, x, normalized=False):
#     """numpy array to MP3"""
#     channels = 2 if (x.ndim == 2 and x.shape[1] == 2) else 1
#     if normalized:  # normalized array - each item should be a float in [-1, 1)
#         y = np.int16(x * 2 ** 15)
#     else:
#         y = np.int16(x)
#     song = AudioSegment(y.tobytes(), frame_rate=sr, sample_width=2, channels=channels)
#     song.export(f, format="mp3", bitrate="320k")

if __name__ == "__main__":
    pass
    # distance(564654654)
    song("Cat Ievan Polkka (320 kbps).wav", "cat320out.wav")
    # sample_rate, data = wavfile.read("Cat Ievan Polkka (320 kbps).wav", "cat320out.wav")

    # for dev in system.devices:
    #     print(f"{dev.name=}")
