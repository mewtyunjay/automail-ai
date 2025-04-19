import { Button } from "@/components/ui/button"
import { MorphingText } from "@/components/ui/morphing-text"
import { ArrowRight, Mail } from "lucide-react"
import Link from "next/link"
import { ScrollReveal } from "@/components/scroll-reveal"
import { FeatureSection } from "@/components/feature-section"

export default function LandingPage() {
  // Using the specified text sequence
  const texts = ["automate", "your", "email", "with", "automail"]

  return (
    <div className="flex flex-col bg-white">
      <header className="container mx-auto flex items-center justify-between p-4">
        <div className="flex items-center gap-2 text-xl font-bold">
          <Mail className="h-6 w-6" />
          <span>AutoMail</span>
        </div>
        <nav>
          <Button variant="ghost" asChild>
            <Link href="/login">Login</Link>
          </Button>
          <Button className="ml-2" asChild>
            <Link href="/dashboard">
              <span>Get Started</span>
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </nav>
      </header>

      <main className="flex flex-col">
        {/* Hero Section */}
        <section className="container mx-auto flex min-h-screen flex-col items-center justify-center px-4 text-center">
          <div className="flex flex-col items-center justify-center w-full mb-8 mt-12 md:mt-0">
            <MorphingText texts={texts} className="text-gray-900" />
          </div>

          <p className="mb-8 max-w-md text-lg text-gray-600">
            Streamline your email workflow with powerful automation tools designed for professionals.
          </p>

          <div className="flex flex-col space-y-4 sm:flex-row sm:space-x-4 sm:space-y-0">
            <Button size="lg" className="px-8" asChild>
              <Link href="/dashboard">Start for free</Link>
            </Button>
            <Button size="lg" variant="outline">
              See how it works
            </Button>
          </div>
        </section>

        {/* Features Section - Appears on scroll */}
        <section className="py-16 bg-gray-50">
          <ScrollReveal>
            <FeatureSection />
          </ScrollReveal>
        </section>
      </main>

      <footer className="border-t border-gray-200 py-6 text-center text-sm text-gray-500">
        <div className="container mx-auto">© {new Date().getFullYear()} AutoMail. All rights reserved.</div>
      </footer>
    </div>
  )
}
