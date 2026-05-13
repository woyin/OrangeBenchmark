interface KanbanBoardProps {
  columns?: Record<string, { id: string; title: string }[]>
}
export default function KanbanBoard(props: KanbanBoardProps) {
  return <div>KanbanBoard</div>
}
