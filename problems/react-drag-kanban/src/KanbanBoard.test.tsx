import { render, screen } from '@testing-library/react'
import KanbanBoard from './KanbanBoard'

const initialData = {
  "To Do": [{ id: "1", title: "Task 1" }, { id: "2", title: "Task 2" }],
  "In Progress": [],
  "Done": [],
}

describe('KanbanBoard', () => {
  test('renders three columns', () => {
    render(<KanbanBoard columns={initialData} />)
    expect(screen.getByText('To Do')).toBeInTheDocument()
    expect(screen.getByText('In Progress')).toBeInTheDocument()
    expect(screen.getByText('Done')).toBeInTheDocument()
  })

  test('renders cards in columns', () => {
    render(<KanbanBoard columns={initialData} />)
    expect(screen.getByText('Task 1')).toBeInTheDocument()
    expect(screen.getByText('Task 2')).toBeInTheDocument()
  })

  test('cards are draggable', () => {
    render(<KanbanBoard columns={initialData} />)
    const cards = screen.getAllByText(/Task/)
    cards.forEach(card => {
      expect(card.closest('[draggable]') || card).toHaveAttribute('draggable')
    })
  })

  test('renders empty columns', () => {
    render(<KanbanBoard />)
    expect(screen.getByText('To Do')).toBeInTheDocument()
  })
})
