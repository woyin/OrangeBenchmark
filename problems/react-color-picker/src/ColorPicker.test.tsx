import { render, screen, fireEvent } from '@testing-library/react'
import ColorPicker from './ColorPicker'

describe('ColorPicker', () => {
  test('renders three sliders', () => {
    render(<ColorPicker />)
    const sliders = screen.getAllByRole('slider')
    expect(sliders.length).toBeGreaterThanOrEqual(3)
  })

  test('displays color preview', () => {
    render(<ColorPicker />)
    expect(screen.getByTestId('color-preview')).toBeInTheDocument()
  })

  test('displays HSL values', () => {
    render(<ColorPicker />)
    expect(screen.getByText(/hsl/i)).toBeInTheDocument()
  })

  test('displays hex code', () => {
    render(<ColorPicker />)
    expect(screen.getByText(/#[0-9a-f]{6}/i)).toBeInTheDocument()
  })

  test('changing hue updates display', () => {
    render(<ColorPicker />)
    const sliders = screen.getAllByRole('slider')
    fireEvent.change(sliders[0], { target: { value: 180 } })
    expect(screen.getByText(/180/)).toBeInTheDocument()
  })
})
