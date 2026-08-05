/**
 * Tests — InputBar, préremplissage "Préparer cette question" (Review Briefing).
 *
 * Couvre les points de la mission GO IMPLEMENT (2026-08-05) :
 *   15. "Préparer cette question" ne déclenche aucun envoi automatique
 *   16. un brouillon existant n'est jamais écrasé
 *   17. aucun préremplissage ne se déclenche sur un simple re-render
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { InputBar, type PrefillToken } from '../InputBar';

function noop() {}

describe('InputBar — préremplissage', () => {
  test('préremplit le champ vide au premier jeton', () => {
    const { rerender } = render(
      <InputBar onSendMessage={noop} onSendFile={noop} prefillToken={null} />
    );
    const textarea = screen.getByPlaceholderText(/Posez une question/i) as HTMLTextAreaElement;
    expect(textarea.value).toBe('');

    const token: PrefillToken = { id: 1, text: 'Quelle est votre décision ?' };
    rerender(<InputBar onSendMessage={noop} onSendFile={noop} prefillToken={token} />);

    expect(textarea.value).toBe('Quelle est votre décision ?');
  });

  test("un brouillon existant n'est jamais écrasé — la question est ajoutée à la suite", () => {
    const { rerender } = render(
      <InputBar onSendMessage={noop} onSendFile={noop} prefillToken={null} />
    );
    const textarea = screen.getByPlaceholderText(/Posez une question/i) as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: 'Mon brouillon existant' } });
    expect(textarea.value).toBe('Mon brouillon existant');

    const token: PrefillToken = { id: 1, text: 'Quelle est votre décision ?' };
    rerender(<InputBar onSendMessage={noop} onSendFile={noop} prefillToken={token} />);

    expect(textarea.value.startsWith('Mon brouillon existant')).toBe(true);
    expect(textarea.value).toContain('Quelle est votre décision ?');
  });

  test("aucun préremplissage ne se déclenche sur un simple re-render (même token.id)", () => {
    const token: PrefillToken = { id: 1, text: 'Quelle est votre décision ?' };
    const { rerender } = render(
      <InputBar onSendMessage={noop} onSendFile={noop} prefillToken={token} />
    );
    const textarea = screen.getByPlaceholderText(/Posez une question/i) as HTMLTextAreaElement;
    expect(textarea.value).toBe('Quelle est votre décision ?');

    // L'utilisateur modifie le texte après le préremplissage.
    fireEvent.change(textarea, { target: { value: "Texte modifié par l'utilisateur" } });
    expect(textarea.value).toBe("Texte modifié par l'utilisateur");

    // Re-render du parent avec le MÊME token (id inchangé) — simule un
    // re-render ordinaire déclenché par un state non lié (ex: isTyping).
    rerender(
      <InputBar
        onSendMessage={noop}
        onSendFile={noop}
        prefillToken={token}
        placeholder="Posez une question de suivi..."
      />
    );

    // Le texte de l'utilisateur ne doit jamais être écrasé par un re-render.
    expect(textarea.value).toBe("Texte modifié par l'utilisateur");
  });

  test('un nouveau clic (nouvel id) déclenche un nouveau préremplissage', () => {
    const token1: PrefillToken = { id: 1, text: 'Question A' };
    const { rerender } = render(
      <InputBar onSendMessage={noop} onSendFile={noop} prefillToken={token1} />
    );
    const textarea = screen.getByPlaceholderText(/Posez une question/i) as HTMLTextAreaElement;
    expect(textarea.value).toBe('Question A');

    fireEvent.change(textarea, { target: { value: '' } });
    const token2: PrefillToken = { id: 2, text: 'Question B' };
    rerender(<InputBar onSendMessage={noop} onSendFile={noop} prefillToken={token2} />);

    expect(textarea.value).toBe('Question B');
  });

  test('le préremplissage ne déclenche jamais onSendMessage — pas d\'envoi automatique', () => {
    const onSendMessage = jest.fn();
    const token: PrefillToken = { id: 1, text: 'Question test' };
    render(<InputBar onSendMessage={onSendMessage} onSendFile={noop} prefillToken={token} />);

    expect(onSendMessage).not.toHaveBeenCalled();
  });

  test('sans prefillToken, le comportement d\'envoi standard reste inchangé', () => {
    const onSendMessage = jest.fn();
    render(<InputBar onSendMessage={onSendMessage} onSendFile={noop} />);
    const textarea = screen.getByPlaceholderText(/Posez une question/i) as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: 'Bonjour' } });
    fireEvent.click(screen.getByTitle('Envoyer (Entrée)'));

    expect(onSendMessage).toHaveBeenCalledWith('Bonjour');
    expect(textarea.value).toBe('');
  });
});
