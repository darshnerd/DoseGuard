import { Alert, Card, Chip, Skeleton } from "@heroui/react";
import { motion } from "framer-motion";
import { ScanLine, Upload } from "lucide-react";
import { useRef, useState, type ChangeEvent } from "react";
import { api, type ScanResponse } from "../api";
import CameraCapture from "../components/CameraCapture";
import { Button } from "@heroui/react";
import { FadeItem, PageHeader, SeverityChip, severityColor } from "../components/ui";

function ResultSkeleton() {
  return (
    <Card>
      <Card.Content>
        <div className="flex flex-col gap-3">
          <Skeleton className="h-5 w-32" />
          <div className="flex gap-2">
            <Skeleton className="h-7 w-20 rounded-full" />
            <Skeleton className="h-7 w-24 rounded-full" />
          </div>
          <Skeleton className="h-16 w-full rounded-xl" />
        </div>
      </Card.Content>
    </Card>
  );
}

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
      <PageHeader icon={ScanLine} title="Scan a label" subtitle="Read a medicine label with your camera." />

      <FadeItem>
        <Card>
          <Card.Header>
            <Card.Title>Read a medicine label</Card.Title>
            <Card.Description>Use your camera or upload a photo.</Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="flex flex-col gap-4">
              <CameraCapture onCapture={handleScan} disabled={loading} />
              <span className="text-sm text-gray-500">or</span>
              <Button variant="secondary" isPending={loading} onPress={() => fileRef.current?.click()}>
                <Upload className="mr-1 size-4" />
                {loading ? "Reading…" : "Upload a photo"}
              </Button>
              <input ref={fileRef} type="file" accept="image/*" hidden onChange={onFile} />
            </div>
          </Card.Content>
        </Card>
      </FadeItem>

      {loading && <ResultSkeleton />}

      {!loading && result && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-6"
        >
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
                    <Alert key={idx} status={severityColor(i.severity)}>
                      <Alert.Indicator />
                      <Alert.Content>
                        <Alert.Title className="flex items-center gap-2">
                          {i.ingredient_a} + {i.ingredient_b}
                          <SeverityChip severity={i.severity} />
                        </Alert.Title>
                        <Alert.Description>{i.description}</Alert.Description>
                      </Alert.Content>
                    </Alert>
                  ))}
                </div>
              )}
            </Card.Content>
          </Card>
        </motion.div>
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
