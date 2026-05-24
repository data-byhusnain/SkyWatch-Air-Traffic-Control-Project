const puppeteer = require('puppeteer');
const fs = require('fs');

const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1080, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            -webkit-print-color-adjust: exact;
        }

        .slide {
            width: 1080px;
            height: 1080px;
            page-break-after: always;
            position: relative;
            background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            box-sizing: border-box;
            padding: 60px;
            border: 10px solid #e2e8f0;
            border-radius: 40px;
        }

        .slide::before {
            content: '';
            position: absolute;
            top: -200px;
            right: -200px;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(14,165,233,0.1) 0%, rgba(255,255,255,0) 70%);
            border-radius: 50%;
            z-index: 0;
        }

        .slide::after {
            content: '';
            position: absolute;
            bottom: -200px;
            left: -200px;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(16,185,129,0.1) 0%, rgba(255,255,255,0) 70%);
            border-radius: 50%;
            z-index: 0;
        }

        .content {
            position: relative;
            z-index: 1;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        h1 {
            font-size: 80px;
            font-weight: 800;
            margin: 0 0 20px 0;
            text-align: center;
            background: linear-gradient(90deg, #0f172a, #334155);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        h2 {
            font-size: 55px;
            font-weight: 800;
            margin: 0 0 50px 0;
            color: #0f172a;
            text-align: center;
        }

        p.subtitle {
            font-size: 35px;
            color: #64748b;
            text-align: center;
            max-width: 800px;
            line-height: 1.5;
            margin-bottom: 50px;
        }

        .image-container {
            width: 100%;
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            box-sizing: border-box;
        }

        img {
            max-width: 95%;
            max-height: 700px;
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);
            object-fit: contain;
        }

        .badges {
            display: flex;
            gap: 20px;
            margin-top: 40px;
        }

        .badge {
            background: #ffffff;
            border: 2px solid #cbd5e1;
            padding: 15px 30px;
            border-radius: 100px;
            font-size: 24px;
            font-weight: 600;
            color: #475569;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        .footer {
            position: absolute;
            bottom: 40px;
            width: 100%;
            text-align: center;
            font-size: 24px;
            color: #94a3b8;
            font-weight: 600;
            z-index: 1;
        }
        
        .cta-box {
            background: white;
            padding: 60px;
            border-radius: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.05);
            text-align: center;
            border: 1px solid #e2e8f0;
            width: 80%;
        }

        .cta-box h3 {
            font-size: 40px;
            margin-top: 0;
            color: #0f172a;
        }

        .cta-box p {
            font-size: 30px;
            color: #3b82f6;
            word-break: break-all;
            margin: 20px 0;
            font-weight: 600;
        }
    </style>
</head>
<body>

    <!-- Slide 1: Title -->
    <div class="slide">
        <div class="content">
            <h1>SkyWatch ATC</h1>
            <p class="subtitle">A Real-Time Air Traffic Control Monitoring System</p>
            <div class="badges">
                <div class="badge">React & Vite</div>
                <div class="badge">Python Flask</div>
                <div class="badge">WebSockets</div>
            </div>
        </div>
    </div>

    <!-- Slide 2: Radar Ops -->
    <div class="slide">
        <div class="content">
            <h2>Live Radar Operations</h2>
            <div class="image-container">
                <img src="file:///C:/Users/ABC/.gemini/antigravity/brain/2493067c-dc5c-40df-a58d-b4e6f89a1e1e/media__1779374260617.png" alt="Radar Ops">
            </div>
            <div class="footer">Smooth real-time aircraft tracking</div>
        </div>
    </div>

    <!-- Slide 3: Collision Engine -->
    <div class="slide">
        <div class="content">
            <h2>Automated Collision Alerts</h2>
            <div class="image-container">
                <img src="file:///C:/Users/ABC/.gemini/antigravity/brain/2493067c-dc5c-40df-a58d-b4e6f89a1e1e/media__1779374260456.png" alt="Collision Engine">
            </div>
            <div class="footer">Mathematical engine triggering RED/YELLOW alerts</div>
        </div>
    </div>

    <!-- Slide 4: Sector Traffic -->
    <div class="slide">
        <div class="content">
            <h2>Sector Traffic Telemetry</h2>
            <div class="image-container">
                <img src="file:///C:/Users/ABC/.gemini/antigravity/brain/2493067c-dc5c-40df-a58d-b4e6f89a1e1e/media__1779374260548.png" alt="Sector Traffic">
            </div>
            <div class="footer">Live altitude, speed, and heading data</div>
        </div>
    </div>

    <!-- Slide 5: Analytics -->
    <div class="slide">
        <div class="content">
            <h2>Global Traffic Insights</h2>
            <div class="image-container">
                <img src="file:///C:/Users/ABC/.gemini/antigravity/brain/2493067c-dc5c-40df-a58d-b4e6f89a1e1e/media__1779374261138.png" alt="Analytics">
            </div>
            <div class="footer">Comprehensive system analytics dashboard</div>
        </div>
    </div>

    <!-- Slide 6: Outro -->
    <div class="slide">
        <div class="content">
            <h2>Explore the Code</h2>
            <div class="cta-box">
                <h3>Open Source Repository</h3>
                <p>github.com/data-byhusnain/SkyWatch-Air-Traffic-Control-Project</p>
            </div>
            <div style="margin-top: 60px; font-size: 30px; font-weight: 600; color: #475569;">
                Created by Husnain
            </div>
        </div>
    </div>

</body>
</html>
`;

(async () => {
    try {
        const browser = await puppeteer.launch();
        const page = await browser.newPage();
        
        await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
        
        await page.pdf({
            path: 'SkyWatch_LinkedIn_Carousel.pdf',
            width: '1080px',
            height: '1080px',
            printBackground: true,
            pageRanges: '1-6'
        });
        
        console.log('PDF Carousel generated successfully as SkyWatch_LinkedIn_Carousel.pdf');
        await browser.close();
    } catch (err) {
        console.error('Error generating PDF:', err);
    }
})();
