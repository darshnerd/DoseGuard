import { Alert, Button, Card, Chip, Input, Modal, Table } from "@heroui/react";
import { History, RotateCw, Trash2 } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { api, type Interaction, type ScanRecord } from "../api";
import { FadeItem, PageHeader, severityColor } from "../components/ui";

function EditModal({ scan }: { scan: ScanRecord }) {
  const [drugs, setDrugs] = useState<string[]>(scan.drugs);
  const [name, setName] = useState("");
  const [results, setResults] = useState<Interaction[] | null>(null);
  const [error, setError] = useState("");

  function add(e: FormEvent) {
    e.preventDefault();
    const value = name.trim().toLowerCase();
    if (value && !drugs.includes(value)) setDrugs([...drugs, value]);
    setName("");
  }

  function remove(d: string) {
    setDrugs(drugs.filter((x) => x !== d));
  }

  async function recheck() {
    setError("");
    try {
      setResults((await api.checkInteractions(drugs)).interactions);
    } catch (err) {
      setError((err as Error).message);
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
                <form className="flex gap-2" onSubmit={add}>
                  <Input fullWidth placeholder="Add a drug" value={name} onChange={(e) => setName(e.target.value)} />
                  <Button type="submit" variant="secondary">
                    Add
                  </Button>
                </form>
                <Button onPress={recheck}>Re-check interactions</Button>

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
                              <EditModal scan={s} />
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
