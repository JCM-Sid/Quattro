import unittest

from quarto import apply_move, is_winning_board, make_piece_set


class QuartoGameTests(unittest.TestCase):
    def test_piece_set_has_sixteen_unique_pieces(self):
        pieces = make_piece_set()
        self.assertEqual(len(pieces), 16)
        self.assertEqual(len(set(pieces)), 16)

    def test_winning_board_detects_a_completed_line(self):
        board = [None] * 16
        board[0] = (0, 0, 0, 0)
        board[1] = (0, 1, 1, 0)
        board[2] = (0, 0, 1, 1)
        board[3] = (0, 1, 0, 1)
        self.assertTrue(is_winning_board(board))

    def test_apply_move_places_piece_and_marks_position(self):
        board = [None] * 16
        piece = (1, 0, 1, 0)
        updated = apply_move(board, piece, 5)
        self.assertEqual(updated[5], piece)
        self.assertIsNone(board[5])
