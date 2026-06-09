import { Alert, Button, Card } from "@heroui/react";
import { motion } from "framer-motion";
import { ArrowRight, CheckCircle2, LayoutDashboard, Pill, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type CheckResponse } from "../api";
import { FadeItem, PageHeader, SeverityChip, Stagger, Stat, severityColor } from "../components/ui";

export default function Dashboard() {
  const [data, setData] = useState<CheckResponse | null>(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api.checkMyMedications().then(setData).catch((e) => setError((e as Error).message));
  }, []);

  const interactions = data?.interactions ?? [];
  const atRisk = interactions.some(
    (i) => i.severity === "contraindicated" || i.severity === "severe"
  );

  return (
    <div className="flex flex-col gap-6">
      <PageHeader icon={LayoutDashboard} title="Dashboard" subtitle="Your medication safety at a glance." />

      <Stagger className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Stat icon={Pill} label="Medications" value={data?.ingredients.length ?? 0} />
        <Stat
          icon={ShieldAlert}
          label="Interactions found"
          value={interactions.length}
          accent={interactions.length ? "text-red-600" : "text-emerald-600"}
        />
        <Stat
          icon={CheckCircle2}
          label="Status"
          value={atRisk ? "At risk" : "OK"}
          accent={atRisk ? "text-red-600" : "text-emerald-600"}
        />
      </Stagger>

      {/* My Day CTA */}
      <FadeItem>
        <Card className="bg-brand-gradient text-white">
          <Card.Content>
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-lg font-semibold">Ready for today?</div>
                <div className="text-sm text-white/80">Log your doses and keep your streak going.</div>
              </div>
              <Button variant="secondary" onPress={() => navigate("/today")}>
                My day <ArrowRight className="ml-1 size-4" />
              </Button>
            </div>
          </Card.Content>
        </Card>
      </FadeItem>

      <FadeItem>
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
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                  >
                    <Alert status={severityColor(i.severity)}>
                      <Alert.Indicator />
                      <Alert.Content>
                        <Alert.Title className="flex items-center gap-2">
                          {i.ingredient_a} + {i.ingredient_b}
                          <SeverityChip severity={i.severity} />
                        </Alert.Title>
                        <Alert.Description>{i.description}</Alert.Description>
                      </Alert.Content>
                    </Alert>
                  </motion.div>
                ))}
              </div>
            )}
          </Card.Content>
        </Card>
      </FadeItem>

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
