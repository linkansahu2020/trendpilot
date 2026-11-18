import { Container } from '@/ui'
import { ClipSourceHub } from './ClipSourceHub'

export default function LandingPage() {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-background py-12 md:py-16">
      <Container className="flex justify-center">
        <ClipSourceHub />
      </Container>
    </main>
  )
}
