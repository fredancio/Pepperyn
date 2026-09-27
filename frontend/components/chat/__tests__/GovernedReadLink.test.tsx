import { fireEvent, render, screen } from '@testing-library/react';
import { GovernedReadLink } from '../GovernedReadLink';
const id = 'e2dc7bd5-c71a-4c88-821c-b1f2696fb04b';
test('no automatic read, exact target and single explicit attempt', () => {
  const read = jest.fn().mockResolvedValue(undefined);
  render(<GovernedReadLink target={id} read={read} />);
  expect(read).not.toHaveBeenCalled();
  const button = screen.getByRole('button');
  fireEvent.click(button); fireEvent.click(button);
  expect(read).toHaveBeenCalledTimes(1);
  expect(read).toHaveBeenCalledWith(id);
  expect(button).toBeDisabled();
});
test.each([null, 'not-a-uuid', '../export.pdf'])('invalid navigation target is inert: %s', target => {
  const read = jest.fn();
  render(<GovernedReadLink target={target} read={read} />);
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
  expect(read).not.toHaveBeenCalled();
});
