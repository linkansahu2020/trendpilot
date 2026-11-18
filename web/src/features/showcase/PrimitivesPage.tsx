import { useState } from 'react'
import {
  Badge,
  Button,
  Card,
  Checkbox,
  Container,
  Input,
  Text,
  Toggle,
} from '@/ui'

export default function PrimitivesPage() {
  const [checked, setChecked] = useState(true)
  const [enabled, setEnabled] = useState(false)

  return (
    <main className="min-h-dvh bg-background py-12 md:py-16">
      <Container className="flex flex-col gap-10">
        <div className="flex flex-col gap-3">
          <Badge showDot tone="accent">
            Luminous Precision
          </Badge>
          <Text variant="headline-lg">UI primitives</Text>
          <Text variant="body-lg">
            Smoke showcase for TrendPilot design tokens and reusable components.
          </Text>
        </div>

        <Card className="flex flex-col gap-6">
          <Text variant="headline-sm">Buttons</Text>
          <div className="flex flex-wrap items-center gap-3">
            <Button>Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="badge" size="sm">
              Badge CTA →
            </Button>
            <Button disabled>Disabled</Button>
          </div>
        </Card>

        <Card className="flex flex-col gap-6">
          <Text variant="headline-sm">Badges</Text>
          <div className="flex flex-wrap items-center gap-3">
            <Badge showDot>AI Powered</Badge>
            <Badge tone="accent">New</Badge>
          </div>
        </Card>

        <Card className="flex flex-col gap-6">
          <Text variant="headline-sm">Input</Text>
          <Input placeholder="Paste a YouTube URL…" />
        </Card>

        <div className="grid gap-6 md:grid-cols-2">
          <Card className="flex flex-col gap-4">
            <Text variant="headline-sm">Standard card</Text>
            <Text variant="body-md">
              White surface, ghost border, soft ambient shadow.
            </Text>
          </Card>
          <Card elevated className="flex flex-col gap-4">
            <Text variant="headline-sm">Elevated card</Text>
            <Text variant="body-md">
              Soft violet glow for featured or focused panels.
            </Text>
          </Card>
        </div>

        <Card className="flex flex-col gap-6">
          <Text variant="headline-sm">Controls</Text>
          <div className="flex flex-wrap items-center gap-8">
            <label className="inline-flex items-center gap-2">
              <Checkbox
                checked={checked}
                onChange={(event) => setChecked(event.target.checked)}
              />
              <Text variant="label">Approve clip</Text>
            </label>
            <label className="inline-flex items-center gap-3">
              <Toggle checked={enabled} onCheckedChange={setEnabled} />
              <Text variant="label">Captions on</Text>
            </label>
          </div>
        </Card>

        <Card className="flex flex-col gap-3">
          <Text variant="caption">CAPTION</Text>
          <Text variant="label">Label</Text>
          <Text variant="body-sm">Body small</Text>
          <Text variant="body-md">Body medium</Text>
          <Text variant="headline-sm">Headline small</Text>
        </Card>
      </Container>
    </main>
  )
}
