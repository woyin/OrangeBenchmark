import { render, screen, fireEvent } from '@testing-library/react'
import FormValidator from './FormValidator'

const fields = [
  { name: 'email', label: 'Email', type: 'email', required: true },
  { name: 'name', label: 'Name', type: 'text', required: true, minLength: 2 },
]

describe('FormValidator', () => {
  test('renders form fields', () => {
    render(<FormValidator fields={fields} onSubmit={() => {}} />)
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Name')).toBeInTheDocument()
  })

  test('shows required error on blur', () => {
    render(<FormValidator fields={fields} onSubmit={() => {}} />)
    const email = screen.getByLabelText('Email')
    fireEvent.blur(email)
    expect(screen.getByText(/required/i)).toBeInTheDocument()
  })

  test('submit button disabled when invalid', () => {
    render(<FormValidator fields={fields} onSubmit={() => {}} />)
    expect(screen.getByText('Submit')).toBeDisabled()
  })

  test('submit enabled when valid', () => {
    render(<FormValidator fields={fields} onSubmit={() => {}} />)
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Bob' } })
    expect(screen.getByText('Submit')).not.toBeDisabled()
  })

  test('calls onSubmit with values', () => {
    const onSubmit = jest.fn()
    render(<FormValidator fields={fields} onSubmit={onSubmit} />)
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Bob' } })
    fireEvent.click(screen.getByText('Submit'))
    expect(onSubmit).toHaveBeenCalled()
  })
})
