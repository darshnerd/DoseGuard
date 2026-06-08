import { Alert, Card, Chip } from "@heroui/react";
import { useEffect, useState } from "react";
import { api, type CheckResponse } from "../api";

const SEVERITY_COLOR: Record<string, "danger" | "warning" | "accent"> = {
  contraindicated: "danger",
  severe: "danger",
  moderate: "warning",
  low: "accent",
};

function Stat({ label, value, accent }: { label: string; value: number | string; accent?: string }) {
  return (
    <Card>
      <Card.Content>
        <div className="text-sm text-gray-500">{label}</div>
        <div className={`mt-1 text-3xl font-bold ${accent ?? ""}`}>{value}</div>
      </Card.Content>
    </Card>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<CheckResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.checkMyMedications().then(setData).catch((e) => setError((e as Error).message));
  }, []);

  const interactions = data?.interactions ?? [];
  const atRisk = interactions.some(
    (i) => i.severity === "contraindicated" || i.severity === "severe"
  );

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Stat label="Medications" value={data?.ingredients.length ?? 0} />
        <Stat
          label="Interactions found"
          value={interactions.length}
          accent={interactions.length ? "text-red-600" : "text-emerald-600"}
        />
        <Stat
          label="Status"
          value={atRisk ? "At risk" : "OK"}
          accent={atRisk ? "text-red-600" : "text-emerald-600"}
        />
      </div>

      <Card>
        <Card.Header>
          <Card.Title>Interactions in your list</Card.Title>
          <Card.Description>Based on your saved medications.</Card.Description>
        </Card.Header>
        <Card.Content>
          {interactions.length === 0 ? (
            <Alert status="success">
              <Alert.Indicator />
              <Alert.Content>
                <Alert.Title>No interactions detected</Alert.Title>
              </Alert.Content>
            </Alert>
          ) : (
            <div className="flex flex-col gap-3">
              {interactions.map((i, idx) => (
                <Alert key={idx} status={SEVERITY_COLOR[i.severity] ?? "accent"}>
                  <Alert.Indicator />
                  <Alert.Content>
                    <Alert.Title className="flex items-center gap-2">
                      {i.ingredient_a} + {i.ingredient_b}
                      <Chip color={SEVERITY_COLOR[i.severity] ?? "accent"}>{i.severity}</Chip>
                    </Alert.Title>
                    <Alert.Description>{i.description}</Alert.Description>
                  </Alert.Content>
                </Alert>
              ))}
            </div>
          )}
        </Card.Content>
      </Card>

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
