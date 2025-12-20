/*
 * SPDX-FileCopyrightText: Copyright (c) 2022 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * SPDX-License-Identifier: MIT
 */

require('dotenv').config({ path: 'env.txt' });

const WebSocket = require('ws');
const path = require('path');
const fs = require('fs');
const https = require('http');
const express = require('express');

const { audioCodesControlMessage, wsServerConnection, wsServerClose }  = require('./modules/audiocodes');

const RivaASRClient = require('./riva_client/asr');

const app = express();
const port = (process.env.PORT);
var server;
var sslkey = './certificates/key.pem';
var sslcert = './certificates/cert.pem';


/**
 * Set up Express Server with CORS and websockets ws
 */
function setupServer() {
    console.log('🚀 Starting server setup...');
    console.log('📁 Static files directory: ./web');
    console.log('🔐 SSL Key path:', sslkey);
    console.log('📜 SSL Cert path:', sslcert);
    
    // set up Express
    app.use(express.static('web')); // ./web is the public dir for js, css, etc.
    console.log('✅ Express static middleware configured');
    
    app.get('/', function (req, res) {
        console.log('📄 Serving index.html to client:', req.ip);
        res.sendFile('./web/index.html', { root: __dirname });
    });
    console.log('✅ Express route handler configured for /');
    
    try {
        console.log('🔍 Reading SSL certificates...');
        const keyData = fs.readFileSync(sslkey);
        const certData = fs.readFileSync(sslcert);
        console.log('✅ SSL certificates loaded successfully');
        
        server = https.createServer(app);
        console.log('✅ HTTPS server created');
    } catch (error) {
        console.error('❌ Failed to load SSL certificates:', error.message);
        console.error('   Make sure certificates exist at:', sslkey, 'and', sslcert);
        process.exit(1);
    }

    const wsServer = new WebSocket.Server({ server });
    console.log('✅ WebSocket server created');

    // Listener, once the client connects to the server socket
    wsServer.on('connection', function connection(ws, req) {
        const clientIP = req.socket.remoteAddress;
        console.log('🔌 New WebSocket connection from:', clientIP);
        wsServerConnection(ws, req);
    });
    
    wsServer.on('close', function close(reason) {
        console.log('📴 WebSocket server closing:', reason);
        wsServerClose(reason)
    });

    wsServer.on('error', function error(err) {
        console.error('❌ WebSocket server error:', err.message);
    });

    server.on('error', function(err) {
        console.error('❌ HTTPS server error:', err.message);
        if (err.code === 'EADDRINUSE') {
            console.error(`   Port ${port} is already in use. Please use a different port.`);
        }
        process.exit(1);
    });

    server.listen(port, () => {
        console.log('🎉 Server successfully started!');
        console.log('🌐 HTTPS Server running on port:', port);
        console.log('🔗 WebSocket Server ready for connections');
        console.log('📍 Access the application at: https://localhost:' + port);
        console.log('🎯 Riva API URL:', process.env.RIVA_API_URL || 'localhost:50051');
    });
};

setupServer();

