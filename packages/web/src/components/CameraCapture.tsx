import { Button } from "@heroui/react";
import { useEffect, useRef, useState } from "react";

interface Props {
  onCapture: (file: File) => void;
  disabled?: boolean;
}

export default function CameraCapture({ onCapture, disabled }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState("");

  async function start() {
    setError("");
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      setStream(s);
    } catch {
      setError("Could not access the camera. Check browser permissions.");
    }
  }

  // Attach the stream AFTER the <video> has mounted, and clean up on stop/unmount.
  useEffect(() => {
    if (!stream) return;
    const video = videoRef.current;
    if (video) {
      video.srcObject = stream;
      video.play().catch(() => undefined);
    }
    return () => stream.getTracks().forEach((track) => track.stop());
  }, [stream]);

  function capture() {
    const video = videoRef.current;
    if (!video || !video.videoWidth) {
      setError("Camera not ready yet — wait a second and try again.");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        onCapture(new File([blob], "capture.jpg", { type: "image/jpeg" }));
        setStream(null);
      },
      "image/jpeg",
      0.9,
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {stream ? (
        <>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full max-w-sm rounded-lg border border-gray-200 bg-black"
          />
          <div className="flex gap-2">
            <Button isDisabled={disabled} onPress={capture}>
              Capture
            </Button>
            <Button variant="tertiary" onPress={() => setStream(null)}>
              Cancel
            </Button>
          </div>
        </>
      ) : (
        <Button variant="secondary" onPress={start}>
          Use camera
        </Button>
      )}
      {error && <p className="text-red-600">{error}</p>}
    </div>
  );
}