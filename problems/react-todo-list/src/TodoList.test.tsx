import { render, screen, fireEvent } from '@testing-library/react'
import TodoList from './TodoList'

describe('TodoList', () => {
  test('renders input and add button', () => {
    render(<TodoList />)
    expect(screen.getByPlaceholderText(/add/i)).toBeInTheDocument()
  })

  test('adds a todo', () => {
    render(<TodoList />)
    const input = screen.getByPlaceholderText(/add/i)
    fireEvent.change(input, { target: { value: 'Buy milk' } })
    fireEvent.submit(input.closest('form')!)
    expect(screen.getByText('Buy milk')).toBeInTheDocument()
  })

  test('toggles todo complete', () => {
    render(<TodoList />)
    const input = screen.getByPlaceholderText(/add/i)
    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.submit(input.closest('form')!)
    fireEvent.click(screen.getByText('Test'))
    expect(screen.getByText('Test')).toHaveClass('completed')
  })

  test('deletes a todo', () => {
    render(<TodoList />)
    const input = screen.getByPlaceholderText(/add/i)
    fireEvent.change(input, { target: { value: 'Delete me' } })
    fireEvent.submit(input.closest('form')!)
    fireEvent.click(screen.getByText(/delete/i))
    expect(screen.queryByText('Delete me')).not.toBeInTheDocument()
  })

  test('filters todos', () => {
    render(<TodoList />)
    const input = screen.getByPlaceholderText(/add/i)
    fireEvent.change(input, { target: { value: 'Task 1' } })
    fireEvent.submit(input.closest('form')!)
    fireEvent.change(input, { target: { value: 'Task 2' } })
    fireEvent.submit(input.closest('form')!)
    fireEvent.click(screen.getByText('Task 1'))
    fireEvent.click(screen.getByText('Active'))
    expect(screen.queryByText('Task 1')).not.toBeInTheDocument()
    expect(screen.getByText('Task 2')).toBeInTheDocument()
  })
})
