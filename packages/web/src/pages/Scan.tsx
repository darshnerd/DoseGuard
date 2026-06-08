import { Alert, Button, Card, Chip } from "@heroui/react";
import { useRef, useState, type ChangeEvent } from "react";
import { api, type ScanResponse } from "../api";
import CameraCapture from "../components/CameraCapture";

const SEVERITY_COLOR: Record<string, "danger" | "warning" | "accent"> = {
  contraindicated: "danger",
  severe: "danger",
  moderate: "warning",
  low: "accent",
};

export default function Scan() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleScan(file: File) {
    setLoading(true);
    setError("");
    try {
      setResult(await api.scan(file));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function onFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleScan(file);
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Scan a label</h1>

      <Card>
        <Card.Header>
          <Card.Title>Read a medicine label</Card.Title>
          <Card.Description>Use your camera or upload a photo.</Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="flex flex-col gap-4">
            <CameraCapture onCapture={handleScan} disabled={loading} />
            <span className="text-sm text-gray-500">or</span>
            <Button
              variant="secondary"
              isPending={loading}
              onPress={() => fileRef.current?.click()}
            >
              {loading ? "Reading…" : "Upload a photo"}
            </Button>
            <input ref={fileRef} type="file" accept="image/*" hidden onChange={onFile} />
          </div>
        </Card.Content>
      </Card>

      {result && (
        <>
          <Card>
            <Card.Header>
              <Card.Title>Detected</Card.Title>
            </Card.Header>
            <Card.Content>
              {result.detected.length === 0 ? (
                <p className="text-gray-500">No drugs recognized. Try a clearer photo.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {result.detected.map((d, idx) => (
                    <Chip key={idx}>{d.ingredient_name ?? d.name}</Chip>
                  ))}
                </div>
              )}
            </Card.Content>
          </Card>

          <Card>
            <Card.Header>
              <Card.Title>Interactions</Card.Title>
            </Card.Header>
            <Card.Content>
              {result.interactions.length === 0 ? (
                <Alert status="success">
                  <Alert.Indicator />
                  <Alert.Content>
                    <Alert.Title>No interactions found</Alert.Title>
                  </Alert.Content>
                </Alert>
              ) : (
                <div className="flex flex-col gap-3">
                  {result.interactions.map((i, idx) => (
                    <Alert key={idx} status={SEVERITY_COLOR[i.severity] ?? "accent"}>
                      <Alert.Indicator />
                      <Alert.Content>
                        <Alert.Title>
                          {i.ingredient_a} + {i.ingredient_b}
                        </Alert.Title>
                        <Alert.Description>{i.description}</Alert.Description>
                      </Alert.Content>
                    </Alert>
                  ))}
                </div>
              )}
            </Card.Content>
          </Card>
        </>
      )}

      {error && (
        <Alert status="danger">
          <Alert.Indicator />
          <Alert.Content>
            <Alert.Title>{error}</Alert.Title>
          </Alert.Content>
        </Alert>
      )}
    </div>
  );
}