"use client"

import type React from "react"

import { useCallback, useEffect, useRef, useState } from "react"

import { cn } from "@/lib/utils"

const morphTime = 0.8
const cooldownTime = 0.3
const initialDelay = 2000 // 2 seconds delay before starting animation

const useMorphingText = (texts: string[]) => {
  const textIndexRef = useRef(0)
  const morphRef = useRef(0)
  const cooldownRef = useRef(0)
  const timeRef = useRef(new Date())
  const animationCompleteRef = useRef(false)
  const [animationStarted, setAnimationStarted] = useState(false)

  const text1Ref = useRef<HTMLSpanElement>(null)
  const text2Ref = useRef<HTMLSpanElement>(null)

  // Initialize with the first text
  useEffect(() => {
    if (text1Ref.current) {
      text1Ref.current.textContent = texts[0]
      text1Ref.current.style.opacity = "100%"
      text1Ref.current.style.filter = "none"
    }
    if (text2Ref.current) {
      text2Ref.current.textContent = texts[1]
      text2Ref.current.style.opacity = "0%"
    }
  }, [texts])

  const setStyles = useCallback(
    (fraction: number) => {
      const [current1, current2] = [text1Ref.current, text2Ref.current]
      if (!current1 || !current2) return

      current2.style.filter = `blur(${Math.min(8 / fraction - 8, 100)}px)`
      current2.style.opacity = `${Math.pow(fraction, 0.4) * 100}%`

      const invertedFraction = 1 - fraction
      current1.style.filter = `blur(${Math.min(8 / invertedFraction - 8, 100)}px)`
      current1.style.opacity = `${Math.pow(invertedFraction, 0.4) * 100}%`

      current1.textContent = texts[textIndexRef.current % texts.length]
      current2.textContent = texts[(textIndexRef.current + 1) % texts.length]
    },
    [texts],
  )

  const doMorph = useCallback(() => {
    // If animation hasn't started or is complete, don't morph
    if (!animationStarted || animationCompleteRef.current) return

    morphRef.current -= cooldownRef.current
    cooldownRef.current = 0

    let fraction = morphRef.current / morphTime

    if (fraction > 1) {
      cooldownRef.current = cooldownTime
      fraction = 1
    }

    setStyles(fraction)

    if (fraction === 1) {
      textIndexRef.current++

      // Check if we've reached the last word ("automail")
      if (textIndexRef.current === texts.length - 1) {
        animationCompleteRef.current = true
      }
    }
  }, [setStyles, texts.length, animationStarted])

  const doCooldown = useCallback(() => {
    // If animation hasn't started, don't do cooldown
    if (!animationStarted) return

    morphRef.current = 0
    const [current1, current2] = [text1Ref.current, text2Ref.current]
    if (current1 && current2) {
      current2.style.filter = "none"
      current2.style.opacity = "100%"
      current1.style.filter = "none"
      current1.style.opacity = "0%"
    }
  }, [animationStarted])

  // Start animation after delay
  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimationStarted(true)
    }, initialDelay)

    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    let animationFrameId: number

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate)

      const newTime = new Date()
      const dt = (newTime.getTime() - timeRef.current.getTime()) / 1000
      timeRef.current = newTime

      cooldownRef.current -= dt

      if (cooldownRef.current <= 0) doMorph()
      else doCooldown()
    }

    animate()
    return () => {
      cancelAnimationFrame(animationFrameId)
    }
  }, [doMorph, doCooldown])

  return { text1Ref, text2Ref }
}

interface MorphingTextProps {
  className?: string
  texts: string[]
}

const Texts: React.FC<Pick<MorphingTextProps, "texts">> = ({ texts }) => {
  const { text1Ref, text2Ref } = useMorphingText(texts)
  return (
    <>
      <span className="absolute inset-0 flex items-center justify-center w-full text-center" ref={text1Ref} />
      <span className="absolute inset-0 flex items-center justify-center w-full text-center" ref={text2Ref} />
    </>
  )
}

const SvgFilters: React.FC = () => (
  <svg id="filters" className="hidden" preserveAspectRatio="xMidYMid slice">
    <defs>
      <filter id="threshold">
        <feColorMatrix
          in="SourceGraphic"
          type="matrix"
          values="1 0 0 0 0
                  0 1 0 0 0
                  0 0 1 0 0
                  0 0 0 255 -140"
        />
      </filter>
    </defs>
  </svg>
)

const MorphingText: React.FC<MorphingTextProps> = ({ texts, className }) => (
  <div
    className={cn(
      "relative mx-auto h-16 w-full max-w-screen-md flex items-center justify-center text-center font-sans text-[40pt] font-bold leading-none [filter:url(#threshold)_blur(0.6px)] md:h-24 lg:text-[6rem]",
      className,
    )}
  >
    <Texts texts={texts} />
    <SvgFilters />
  </div>
)

export { MorphingText }
