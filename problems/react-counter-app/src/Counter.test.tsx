import { render, screen, fireEvent } from '@testing-library/react'
import Counter from './Counter'

describe('Counter', () => {
  test('renders initial count of 0', () => {
    render(<Counter />)
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  test('increments count', () => {
    render(<Counter />)
    fireEvent.click(screen.getByText('+'))
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  test('decrements count but not below 0', () => {
    render(<Counter />)
    fireEvent.click(screen.getByText('-'))
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  test('resets count', () => {
    render(<Counter />)
    fireEvent.click(screen.getByText('+'))
    fireEvent.click(screen.getByText('+'))
    fireEvent.click(screen.getByText('Reset'))
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  test('increment and decrement cycle', () => {
    render(<Counter />)
    fireEvent.click(screen.getByText('+'))
    fireEvent.click(screen.getByText('+'))
    fireEvent.click(screen.getByText('+'))
    expect(screen.getByText('3')).toBeInTheDocument()
    fireEvent.click(screen.getByText('-'))
    expect(screen.getByText('2')).toBeInTheDocument()
  })
})
