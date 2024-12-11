import sys
import serial
import sqlite3
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTabWidget, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QTextEdit, QProgressBar, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor


class DrumControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.playing = False
        self.initDB()
        self.initUI()
        self.updateTime()

    def initUI(self):
        self.setWindowTitle('Drum Control')
        self.setGeometry(100, 100, 600, 400)

        self.tabs = QTabWidget()
        self.connection_tab = QWidget()
        self.play_tab = QWidget()
        self.melody_tab = QWidget()

        self.tabs.addTab(self.connection_tab, 'Подключение')
        self.tabs.addTab(self.play_tab, 'Проигрывание')
        self.tabs.addTab(self.melody_tab, 'Мелодии')

        self.initConnectionTab()
        self.initPlayTab()
        self.initMelodyTab()

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def initDB(self):
        self.conn = sqlite3.connect('melodies.db')
        self.curs = self.conn.cursor()
        self.curs.execute('''
            CREATE TABLE IF NOT EXISTS melody (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                length INTEGER,
                time INTEGER,
                sequence TEXT
            )
        ''')
        self.conn.commit()

    def initConnectionTab(self):
        layout = QVBoxLayout()

        self.com_port_label = QLabel('COM порт:', self)
        self.com_port_input = QLineEdit(self)
        self.com_port_input.setText('COM6')

        self.baud_rate_label = QLabel('Частота:', self)
        self.baud_rate_input = QLineEdit(self)
        self.baud_rate_input.setText('9600')

        self.connect_button = QPushButton('Подключить', self)
        self.connect_button.clicked.connect(self.connect_serial)

        self.disconnect_button = QPushButton('Отключить', self)
        self.disconnect_button.clicked.connect(self.disconnect_serial)

        self.status_label = QLabel('Отключено', self)
        self.status_label.setStyleSheet('color: red')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)

        layout.addWidget(self.com_port_label)
        layout.addWidget(self.com_port_input)
        layout.addWidget(self.baud_rate_label)
        layout.addWidget(self.baud_rate_input)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_text)

        self.connection_tab.setLayout(layout)

    def initPlayTab(self):
        layout = QVBoxLayout()

        self.melody_combo = QComboBox(self)
        self.melody_combo.addItems(self.load_melodies())
        self.melody_combo.currentIndexChanged.connect(self.updateTime)

        self.play_button = QPushButton('Проиграть', self)
        self.play_button.clicked.connect(self.play_melody)

        self.times_label = QLabel('Повторений:', self)
        self.times_spinbox = QSpinBox(self)
        self.times_spinbox.setMinimum(1)
        self.times_spinbox.setMaximum(100)
        self.times_spinbox.valueChanged.connect(self.updateTime)

        layout_times = QHBoxLayout()
        layout_times.addWidget(self.times_label)
        layout_times.addWidget(self.times_spinbox)

        self.itg_time_label2 = QLabel('Секунды:', self)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)

        layout.addWidget(self.melody_combo)
        layout.addLayout(layout_times)
        layout.addWidget(self.itg_time_label2)
        layout.addWidget(self.play_button)
        layout.addWidget(self.progress_bar)

        self.play_tab.setLayout(layout)

    def initMelodyTab(self):
        layout = QVBoxLayout()

        self.melody_name_label = QLabel('Название мелодии:', self)
        self.melody_name_input = QLineEdit(self)

        self.length_label = QLabel('Длина:', self)
        self.length_spinbox = QSpinBox(self)
        self.length_spinbox.setMinimum(2)
        self.length_spinbox.setMaximum(2000)
        self.length_spinbox.valueChanged.connect(self.update_table)

        self.time_label = QLabel('Время:', self)
        self.time_spinbox = QSpinBox(self)
        self.time_spinbox.setMinimum(200)
        self.time_spinbox.setMaximum(1000)
        self.time_spinbox.valueChanged.connect(self.updateTime)

        self.itg_time_label = QLabel('Секунды:', self)

        self.table = QTableWidget(self)
        self.table.setRowCount(4)
        self.table.setColumnCount(self.length_spinbox.value())
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.cellClicked.connect(self.cell_clicked)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for i in range(self.table.columnCount()):
            self.table.setColumnWidth(i, 10)

        self.clear_button = QPushButton('Отчистить', self)
        self.clear_button.clicked.connect(self.clear)

        self.generate_button = QPushButton('Сохранить', self)
        self.generate_button.clicked.connect(self.save_melody)

        self.edit_button = QPushButton('Редактировать', self)
        self.edit_button.clicked.connect(self.show_edit_combo)

        self.edit_combo = QComboBox(self)
        self.edit_combo.addItems(self.load_melodies())
        self.edit_combo.setVisible(False)
        self.edit_combo.currentIndexChanged.connect(self.load_melody_for_edit)

        self.delete_button = QPushButton('Удалить', self)
        self.delete_button.setVisible(False)
        self.delete_button.clicked.connect(self.confirm_delete_melody)

        layout.addWidget(self.melody_name_label)
        layout.addWidget(self.melody_name_input)
        layout.addWidget(self.length_label)
        layout.addWidget(self.length_spinbox)
        layout.addWidget(self.time_label)
        layout.addWidget(self.time_spinbox)
        layout.addWidget(self.itg_time_label)
        layout.addWidget(self.table)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.edit_combo)
        layout.addWidget(self.delete_button)

        self.melody_tab.setLayout(layout)

    def connect_serial(self):
        com_port = self.com_port_input.text()
        baud_rate = int(self.baud_rate_input.text())
        try:
            self.serial_port = serial.Serial(com_port, baud_rate, timeout=1)
            self.status_label.setText('Подключено')
            self.status_label.setStyleSheet('color: green')
            self.log('Подключено к ' + com_port + ' на ' + str(baud_rate))
        except serial.SerialException as e:
            self.log('Ошибка подключения: ' + str(e))

    def disconnect_serial(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.status_label.setText('Отключено')
            self.status_label.setStyleSheet('color: red')
            self.log('Отключено')

    def play_melody(self):
        if not self.serial_port or not self.serial_port.is_open:
            self.log('Ошибка: нет соединения')
            return

        if self.playing:
            self.log('Ошибка: мелодия уже играет')
            return

        melody_name = self.melody_combo.currentText()
        melody_data = self.load_melody(melody_name, self.times_spinbox.value())
        if melody_data:
            command = f"PLAY:{melody_data}"
            self.log(f'>> {command}')
            self.serial_port.write((command + '\n').encode())
            self.serial_port.flush()
            self.playing = True
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(int(melody_data.split(':')[0]))
            self.progress_bar.setValue(0)
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_progress)
            self.timer.start(int(melody_data.split(':')[1]) // 2)

    def update_progress(self):
        if self.serial_port and self.serial_port.is_open:
            response = self.serial_port.readline().decode().strip()
            if response == 'Status 1':
                self.playing = False
                self.progress_bar.setVisible(False)
                self.timer.stop()
                self.log('Мелодия завершена')
            elif response.startswith('bit'):
                i = response.split(',')[1]
                self.log(f'удар {i}: {response.split(',')[2]}')
                self.progress_bar.setValue(self.progress_bar.value() + 1)

    def load_melodies(self):
        self.curs.execute('SELECT name FROM melody')
        melodies = self.curs.fetchall()
        return [melody[0] for melody in melodies]

    def confirm_delete_melody(self):
        melody_name = self.melody_name_input.text()
        reply = QMessageBox.question(
            self, 'Подтверждение', f'Вы уверены, что хотите удалить мелодию "{melody_name}"?')
        print(reply)
        if reply == 16384:
            self.delete_melody(melody_name)

    def delete_melody(self, melody_name):
        self.curs.execute(
            'DELETE FROM melody WHERE name = ?', (melody_name,))
        self.conn.commit()
        self.log(f'Мелодия "{melody_name}" удалена')
        self.melody_combo.removeItem(self.melody_combo.findText(melody_name))
        self.edit_combo.removeItem(self.edit_combo.findText(melody_name))

    def load_melody(self, melody_name, times=1):
        self.curs.execute(
            'SELECT length, time, sequence FROM melody WHERE name = ?', (melody_name,))
        melody = self.curs.fetchone()
        if melody:
            return f"{melody[0] * times}:{melody[1]}:{melody[2] * times}"
        return None

    def show_edit_combo(self):
        visible = self.edit_combo.isVisible()
        self.edit_combo.setVisible(not visible)
        self.delete_button.setVisible(not visible)
        if not visible:
            self.load_melody_for_edit(0)

    def load_melody_for_edit(self, index):
        melody_name = self.edit_combo.itemText(index)
        melody_data = self.load_melody(melody_name)
        if melody_data:
            length, time, sequence = melody_data.split(':')
            self.melody_name_input.setText(melody_name)
            self.length_spinbox.setValue(int(length))
            self.time_spinbox.setValue(int(time))
            self.update_table()
            for i in range(self.table.columnCount()):
                for j in range(self.table.rowCount()):
                    bit = sequence[i * 4 + j]
                    item = QTableWidgetItem(bit)
                    item.setBackground(
                        QColor(0, 0, 0) if bit == '1' else QColor(255, 255, 255))
                    self.table.setItem(j, i, item)
            self.log(f'Мелодия "{melody_name}" загружена для редактирования')
        else:
            self.log(f'Мелодия "{melody_name}" не найдена')

    def updateTime(self):
        self.itg_time_label.setText(
            'Секунды: ' + str(self.length_spinbox.value() * self.time_spinbox.value() / 1000))
        melody_name = self.melody_combo.currentText()
        try:
            melody_data = list(map(int, self.load_melody(
                melody_name, self.times_spinbox.value()).split(':')))
            time = (melody_data[0] * melody_data[1]) / 1000
            self.itg_time_label2.setText(
                'Секунды: ' + str(time))
        except AttributeError:
            self.itg_time_label2.setText(
                'Секунды: ?')

    def update_table(self):
        self.updateTime()
        self.table.setColumnCount(self.length_spinbox.value())
        for i in range(self.table.columnCount()):
            self.table.setColumnWidth(i, 10)
            for j in range(self.table.rowCount()):
                item = self.table.item(j, i)
                if item is None:
                    item = QTableWidgetItem('0')
                    item.setBackground(QColor(255, 255, 255))
                    self.table.setItem(j, i, item)

    def cell_clicked(self, row, column):
        item = self.table.item(row, column)
        if item is None:
            item = QTableWidgetItem('1')
            item.setBackground(QColor(0, 0, 0))
            self.table.setItem(row, column, item)
        elif item.text() == '0':
            item.setText('1')
            item.setBackground(QColor(0, 0, 0))
        else:
            item.setText('0')
            item.setBackground(QColor(255, 255, 255))

    def clear(self):
        for i in range(self.table.columnCount()):
            self.table.setColumnWidth(i, 10)
            for j in range(self.table.rowCount()):
                item = self.table.item(j, i)
                item = QTableWidgetItem('0')
                item.setBackground(QColor(255, 255, 255))
                self.table.setItem(j, i, item)

    def save_melody(self):
        data = [[self.length_spinbox.value()], [self.time_spinbox.value()], [
            0], [0]]
        for i in range(self.table.columnCount()):
            for j in range(self.table.rowCount()):
                item = self.table.item(j, i)
                if item is None:
                    data[j].append(0)
                else:
                    data[j].append(int(item.text()))

        melody_name = self.melody_name_input.text()
        bits = []
        for sti in range(1, len(data[0])):
            for row in data:
                bits.append(str(row[sti]))
        sequence = ''.join(bits)

        self.curs.execute(
            f'''SELECT name FROM melody WHERE name == "{melody_name}"''')
        res = self.curs.fetchone()
        if res is None:
            self.curs.execute('INSERT INTO melody (name, length, time, sequence) VALUES (?, ?, ?, ?)',
                              (melody_name, self.length_spinbox.value(), self.time_spinbox.value(), sequence))
            self.conn.commit()
            self.melody_combo.addItem(melody_name)
            self.edit_combo.addItem(melody_name)
        else:
            self.curs.execute(f'UPDATE melody SET (name, length, time, sequence) = (?, ?, ?, ?) WHERE name == "{melody_name}"',
                              (melody_name, self.length_spinbox.value(), self.time_spinbox.value(), sequence))
            self.conn.commit()
        self.log(f'Мелодия "{melody_name}" сохранена')

    def log(self, message):
        self.log_text.append(message)


def main():
    app = QApplication(sys.argv)
    ex = DrumControlApp()
    ex.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
