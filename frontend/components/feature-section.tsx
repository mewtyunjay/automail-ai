"use client"

import { FeatureSteps } from "@/components/ui/feature-steps"

const features = [
  {
    step: "Step 1",
    title: "Auto Label Email",
    content: "Automatically create labels based on natural language to know what's important.",
    image: "https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?q=80&w=1000&auto=format&fit=crop",
  },
  {
    step: "Step 2",
    title: "Create insights that you'd normally miss",
    content: "Get financial statements, reminders, and to-dos, right on your homescreen",
    image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1000&auto=format&fit=crop",
  },
  {
    step: "Step 3",
    title: "Auto Draft Response",
    content: "Auto generate responses which learn from you over time.",
    image: "https://images.unsplash.com/photo-1596526131083-e8c633c948d2?q=80&w=1000&auto=format&fit=crop",
  },
]

export function FeatureSection() {
  return (
    <FeatureSteps
      features={features}
      title="Your Second Brain for Email"
      autoPlayInterval={4000}
      imageHeight="h-[500px]"
    />
  )
}
