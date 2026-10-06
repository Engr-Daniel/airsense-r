const placeholderX = Array.from({length: 24}, (_, i) => i);
const actual = placeholderX.map(i => 45 + 12*Math.sin(i/3) + i*0.25);
const predicted = actual.map((v,i) => v + 4*Math.sin(i/2.2));

Plotly.newPlot('prediction-chart', [
  {x: placeholderX, y: actual, mode: 'lines', name: 'Actual'},
  {x: placeholderX, y: predicted, mode: 'lines', name: 'Predicted'}
], {margin:{t:20,r:20,b:45,l:55}, xaxis:{title:'Time index'}, yaxis:{title:'PM2.5'}, legend:{orientation:'h'}}, {responsive:true});

Plotly.newPlot('comparison-chart', [
  {x:['Persistence','XGBoost','MLP','GRU'], y:[0,0,0,0], type:'bar', name:'MAE'}
], {margin:{t:20,r:20,b:45,l:55}, yaxis:{title:'MAE'}, annotations:[{text:'Results will populate after experiments', x:1.5, y:0, showarrow:false, yshift:30}]}, {responsive:true});

// Replace placeholders by loading exported artifacts from docs/data/ after experiments.
