import { Alert, Button, Card, Chip, Modal, Table } from "@heroui/react";
import { History, RotateCw, Save, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type Interaction, type ScanRecord } from "../api";
import DrugSearch from "../components/DrugSearch";
import { FadeItem, PageHeader, severityColor } from "../components/ui";

function EditModal({ scan, onSaved }: { scan: ScanRecord; onSaved: () => void }) {
  const [drugs, setDrugs] = useState<string[]>(scan.drugs);
  const [results, setResults] = useState<Interaction[] | null>(null);
  const [error, setError] = useState("");
  const [rechecking, setRechecking] = useState(false);
  const [saving, setSaving] = useState(false);

  function remove(d: string) {
    setDrugs(drugs.filter((x) => x !== d));
  }

  async function recheck() {
    setError("");
    setRechecking(true);
    try {
      setResults((await api.checkInteractions(drugs)).interactions);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setRechecking(false);
    }
  }

  async function save() {
    setError("");
    setSaving(true);
    try {
      await api.updateScan(scan.id, drugs);
      onSaved();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal>
      <Button size="sm" variant="secondary">
        <RotateCw className="mr-1 size-4" /> Edit & re-check
      </Button>
      <Modal.Backdrop>
        <Modal.Container>
          <Modal.Dialog className="sm:max-w-[520px]">
            <Modal.CloseTrigger />
            <Modal.Header>
              <Modal.Heading>Edit extracted drugs</Modal.Heading>
            </Modal.Header>
            <Modal.Body>
              <div className="flex flex-col gap-4">
                <div className="flex flex-wrap gap-2">
                  {drugs.length === 0 && <span className="text-gray-500">No drugs.</span>}
                  {drugs.map((d) => (
                    <Chip key={d}>
                      {d}
                      <button className="ml-1" onClick={() => remove(d)}>
                        ✕
                      </button>
                    </Chip>
                  ))}
                </div>

                <DrugSearch
                  onSearch={api.searchDrugs}
                  onSelect={(hit) => {
                    const v = hit.normalized.toLowerCase();
                    if (!drugs.includes(v)) setDrugs([...drugs, v]);
                  }}
                  placeholder="Add a drug"
                />

                <div className="flex gap-2">
                  <Button
                    onPress={recheck}
                    isPending={rechecking}
                    isDisabled={rechecking || drugs.length === 0}
                  >
                    {rechecking ? "Checking…" : "Re-check interactions"}
                  </Button>
                  <Button variant="secondary" onPress={save} isPending={saving} isDisabled={saving}>
                    <Save className="mr-1 size-4" /> {saving ? "Saving…" : "Save"}
                  </Button>
                </div>

                {results &&
                  (results.length === 0 ? (
                    <Alert status="success">
                      <Alert.Indicator />
                      <Alert.Content>
                        <Alert.Title>No interactions found</Alert.Title>
                      </Alert.Content>
                    </Alert>
                  ) : (
                    <div className="flex flex-col gap-2">
                      {results.map((i, idx) => (
                        <Alert key={idx} status={severityColor(i.severity)}>
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
                  ))}
                {error && <p className="text-red-600">{error}</p>}
              </div>
            </Modal.Body>
            <Modal.Footer>
              <Button slot="close" variant="tertiary">
                Close
              </Button>
            </Modal.Footer>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal>
  );
}

export default function Scans() {
  const [scans, setScans] = useState<ScanRecord[]>([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      setScans(await api.listScans());
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function remove(id: number) {
    await api.deleteScan(id);
    load();
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader icon={History} title="Scan history" subtitle="Your previous label scans." />
      <FadeItem>
        <Card>
          <Card.Content>
            {scans.length === 0 ? (
              <p className="text-gray-500">No scans yet. Scan a label to see it here.</p>
            ) : (
              <Table>
                <Table.ScrollContainer>
                  <Table.Content aria-label="Scan history" className="min-w-[640px]">
                    <Table.Header>
                      <Table.Column isRowHeader>Date</Table.Column>
                      <Table.Column>Extracted drugs</Table.Column>
                      <Table.Column>Interactions</Table.Column>
                      <Table.Column>Status</Table.Column>
                      <Table.Column>Actions</Table.Column>
                    </Table.Header>
                    <Table.Body>
                      {scans.map((s) => (
                        <Table.Row key={s.id}>
                          <Table.Cell>{new Date(s.created_at).toLocaleString()}</Table.Cell>
                          <Table.Cell>{s.drugs.join(", ") || "—"}</Table.Cell>
                          <Table.Cell>{s.interaction_count}</Table.Cell>
                          <Table.Cell>
                            <Chip color={s.conflict_found ? "danger" : "success"}>
                              {s.conflict_found ? "At risk" : "OK"}
                            </Chip>
                          </Table.Cell>
                          <Table.Cell>
                            <div className="flex gap-2">
                              <EditModal scan={s} onSaved={load} />
                              <Button size="sm" variant="danger" onPress={() => remove(s.id)}>
                                <Trash2 className="mr-1 size-4" /> Delete
                              </Button>
                            </div>
                          </Table.Cell>
                        </Table.Row>
                      ))}
                    </Table.Body>
                  </Table.Content>
                </Table.ScrollContainer>
              </Table>
            )}
          </Card.Content>
        </Card>
      </FadeItem>
      {error && <p className="text-red-600">{error}</p>}
    </div>
  );
}
