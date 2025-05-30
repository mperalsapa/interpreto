// src/components/MediaViewer.jsx
import { useCallback, useEffect, useState, useRef } from "react";

export default function MediaViewer({
  fileUrl,
  transcription,
  generateVTTCallback,
  onCueChange,
  contentType = "video",
}) {
  const [vttUrl, setVttUrl] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volumeLevel, setVolumeLevel] = useState(1);
  const [OverlayText, setOverlayText] = useState("");
  const videoRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
      setDuration(video.duration);
    };
    const handlePlay = () => setPlaying(true);
    const handlePause = () => setPlaying(false);
    const handleEnded = () => setPlaying(false);

    video.addEventListener("timeupdate", handleTimeUpdate);
    video.addEventListener("play", handlePlay);
    video.addEventListener("pause", handlePause);
    video.addEventListener("ended", handleEnded);

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
      video.removeEventListener("play", handlePlay);
      video.removeEventListener("pause", handlePause);
      video.removeEventListener("ended", handleEnded);
    };
  }, [videoRef]);

  useEffect(() => {
    if (transcription && transcription.length) {
      let vtt = generateVTTCallback(transcription);
      setVttUrl(URL.createObjectURL(new Blob([vtt], { type: "text/vtt" })));
    }
  }, [transcription]);

  const togglePlay = () => {
    const video = videoRef.current;
    if (video) {
      if (playing) {
        video.pause();
      } else {
        if (video.currentTime == video.duration) {
          video.currentTime = 0;
        }
        video.play();
      }
    }
  };

  const seek = useCallback((time, absolute = false) => {
    const video = videoRef.current;
    if (video) {
      let nextTime = absolute ? time : video.currentTime + time;
      nextTime = Math.max(0, Math.min(nextTime, video.duration));
      video.currentTime = nextTime;
    }
  }, []);

  const volume = useCallback((vol) => {
    const video = videoRef.current;
    if (video) {
      video.volume = vol;
      setVolumeLevel(vol);
    }
  });

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600)
      .toString()
      .padStart(2, "0");
    const mins = Math.floor((seconds % 3600) / 60)
      .toString()
      .padStart(2, "0");
    const secs = Math.floor(seconds % 60)
      .toString()
      .padStart(2, "0");
    return `${hrs}:${mins}:${secs}`;
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (!video.textTracks || !video.textTracks.length) return;

    const track = video.textTracks[0];
    const handleCueChange = () => {
      const cue = track.activeCues[0];
      setOverlayText(cue ? cue.text : "");
      if (cue) {
        if (typeof onCueChange === "function") {
          onCueChange(cue);
        }
      }
    };

    track.oncuechange = handleCueChange;

    return () => {
      track.oncuechange = null;
    };
  }, [vttUrl]);

  return (
    <div className="rounded-lg bg-white p-6 shadow-lg dark:bg-gray-800">
      <div className="relative">
        {OverlayText && (
          <div
            className={`absolute bottom-0 flex w-full items-center justify-center ${contentType != "video" ? "top-0" : "pb-8"}`}
          >
            <p className="h-fit w-fit max-w-9/10 bg-black px-2 py-1 text-center text-xl text-white">
              {OverlayText}
            </p>
          </div>
        )}
        <video
          onClick={togglePlay}
          ref={videoRef}
          className="w-full rounded-t-lg bg-gray-900"
        >
          <source src={fileUrl} />
          {vttUrl && <track src={vttUrl} kind="metadata" default />}
        </video>
      </div>
      <div className="rounded-b-lg bg-gray-100 px-5 py-4 dark:bg-gray-900">
        <input
          onChange={(e) => seek(e.target.value, true)}
          className="w-full"
          type="range"
          min="0"
          max={duration}
          value={currentTime}
        />
        <div className="flex w-full items-center justify-between">
          <div className="flex gap-3">
            <button onClick={() => seek(-5)} className="hidden-48 size-[24px]">
              <span className="material-symbols-outlined inline-icon">
                fast_rewind
              </span>
            </button>
            <button onClick={togglePlay} className="size-[24px]">
              <span className="material-symbols-outlined inline-icon">
                {playing ? "pause" : "play_arrow"}
              </span>
            </button>
            <button onClick={() => seek(5)} className="hidden-48 size-[24px]">
              <span className="material-symbols-outlined inline-icon">
                fast_forward
              </span>
            </button>
            <span className="hidden-44">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>
          <div className="flex gap-3">
            <div className="hidden-34 flex">
              <button
                onClick={() => {
                  volumeLevel > 0 ? volume(0) : volume(0.5);
                }}
                className="size-[24px]"
              >
                <span
                  className="material-symbols-outlined inline-icon"
                  id="volume-icon"
                >
                  {volumeLevel > 0 ? "volume_up" : "volume_off"}
                </span>
              </button>
              <input
                onChange={(e) => {
                  volume(e.target.value);
                }}
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={volumeLevel}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
