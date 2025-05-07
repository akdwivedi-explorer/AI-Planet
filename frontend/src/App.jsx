import './App.css';
import { MdOutlineAddCircleOutline } from "react-icons/md";
import { LuSendHorizontal } from "react-icons/lu";
import { useRef, useState } from 'react';
import logo from "./assets/logo.png";
import axios from 'axios';

function App() {
  const [message, setMessage] = useState('');
  const [chat, setChat] = useState([]);
  const [documentId, setDocumentId] = useState(null);
  const [selectedFileName, setSelectedFileName] = useState(''); // State for file name
  const fileInputRef = useRef(null);

  const handleUploadClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setSelectedFileName(file.name); // Set the file name

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post('http://localhost:8000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setDocumentId(res.data.document_id);
      alert("PDF uploaded successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to upload PDF.");
    }
  };

  const handleSend = async () => {
    if (!message.trim()) return;
    if (!documentId) {
      alert("Please upload a PDF first.");
      return;
    }

    const newChat = [...chat, { type: 'user', text: message }];
    setChat(newChat);
    setMessage('');

    try {
      const res = await axios.post('http://localhost:8000/ask', {
        document_id: documentId,
        question: message,
      });

      setChat([...newChat, { type: 'bot', text: res.data.answer }]);
    } catch (err) {
      console.error(err);
      setChat([...newChat, { type: 'bot', text: "Error getting response." }]);
    }
  };

  return (
    <>
      <header className='flex justify-between items-center p-6 shadow-md'>
        <div>
          <img src={logo} alt="AI Planet" />
        </div>
        <div className='flex items-center gap-4'>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
          <button
            onClick={handleUploadClick}
            className='border cursor-pointer rounded-lg p-2 flex items-center gap-2 hover:shadow-md hover:transition-shadow'
          >
            <MdOutlineAddCircleOutline /> <span>Upload PDF</span>
          </button>
          {selectedFileName && (
            <span className='text-sm text-gray-600 italic'>Selected: {selectedFileName}</span>
          )}
        </div>
      </header>

      <main className='flex flex-col justify-between h-[calc(100vh-100px)]'>
        <div className='flex-1 flex flex-col items-center justify-start p-4 gap-2 overflow-y-auto'>
          {chat.map((msg, index) => (
            <div key={index} className={`p-2 rounded-lg max-w-[70%] ${msg.type === 'user' ? 'bg-blue-100 self-end' : 'bg-gray-200 self-start'}`}>
              {msg.text}
            </div>
          ))}
        </div>

        <div className='w-full flex items-end justify-center px-4 pb-6'>
          <div className='flex items-end w-[80%] bg-[#E4E8EE] rounded-lg p-2 shadow-md gap-2'>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={1}
              placeholder='Send a message'
              className='flex-grow bg-transparent resize-none outline-none'
              onInput={(e) => {
                e.target.style.height = 'auto';
                e.target.style.height = e.target.scrollHeight + 'px';
              }}
            />
            <button type='submit' onClick={handleSend}><LuSendHorizontal className='text-2xl cursor-pointer' /></button>
          </div>
        </div>
      </main>
    </>
  );
}

export default App;
