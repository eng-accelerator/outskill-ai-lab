import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'

interface ResearchReportProps {
  content: string
  isStreaming?: boolean
}

export function ResearchReport({ content, isStreaming = false }: ResearchReportProps) {
  if (!content) return null

  return (
    <div className="w-full">
      <article className={cn(
        'prose prose-invert prose-sm max-w-none',
        'prose-headings:text-foreground prose-headings:font-semibold',
        'prose-h1:text-2xl prose-h1:mb-4 prose-h1:mt-8',
        'prose-h2:text-xl prose-h2:mb-3 prose-h2:mt-6',
        'prose-h3:text-lg prose-h3:mb-2 prose-h3:mt-4',
        'prose-p:text-foreground/90 prose-p:leading-relaxed prose-p:mb-4',
        'prose-a:text-primary prose-a:no-underline hover:prose-a:underline',
        'prose-strong:text-foreground prose-strong:font-semibold',
        'prose-ul:text-foreground/90 prose-ol:text-foreground/90',
        'prose-li:mb-1',
        'prose-blockquote:border-primary/40 prose-blockquote:text-muted-foreground',
        'prose-code:text-primary prose-code:bg-primary/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm',
        'prose-pre:bg-muted prose-pre:border prose-pre:border-border',
      )}>
        <ReactMarkdown>{content}</ReactMarkdown>
        {isStreaming && <BlinkingCursor />}
      </article>
    </div>
  )
}

function BlinkingCursor() {
  return (
    <span className="inline-block w-0.5 h-5 bg-primary ml-0.5 align-text-bottom animate-blink" />
  )
}
