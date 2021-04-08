function love.load()

  love.mouse.setRelativeMode(true)

  love.physics.setMeter(64) --the height of a meter our worlds will be 64px
  world = love.physics.newWorld(0, 0, true) --create a world for the bodies to exist in with horizontal gravity of 0 and vertical gravity of 9.81

  sensitivity = 0.011
  rotationAngle = 0
  aimLength = 100

  width = 650
  height = 650


   objects = {} -- table to hold all our physical objects

   barrierThickness = 50
  
  --let's create the bottom
  objects.bottom = {}
  objects.bottom.body = love.physics.newBody(world, width/2, height-(barrierThickness/2)) --remember, the shape (the rectangle we create next) anchors to the body from its center, so we have to move it to (650/2, 650-50/2)
  objects.bottom.shape = love.physics.newRectangleShape(width, barrierThickness) --make a rectangle with a width of height and a height of 50
  objects.bottom.fixture = love.physics.newFixture(objects.bottom.body, objects.bottom.shape) --attach shape to body

  --let's create the top
  objects.top = {}
  objects.top.body = love.physics.newBody(world, width/2, (barrierThickness/2)) --remember, the shape (the rectangle we create next) anchors to the body from its center, so we have to move it to (650/2, 650-50/2)
  objects.top.shape = love.physics.newRectangleShape(width, barrierThickness) --make a rectangle with a width of height and a height of 50
  objects.top.fixture = love.physics.newFixture(objects.top.body, objects.top.shape) --attach shape to body

  --let's create the right
  objects.right = {}
  objects.right.body = love.physics.newBody(world, width-(barrierThickness/2), height/2) --remember, the shape (the rectangle we create next) anchors to the body from its center, so we have to move it to (650/2, 650-50/2)
  objects.right.shape = love.physics.newRectangleShape(barrierThickness, height) --make a rectangle with a width of height and a height of 50
  objects.right.fixture = love.physics.newFixture(objects.right.body, objects.right.shape) --attach shape to body

  --let's create the left
  objects.left = {}
  objects.left.body = love.physics.newBody(world, (barrierThickness/2), height/2) --remember, the shape (the rectangle we create next) anchors to the body from its center, so we have to move it to (650/2, 650-50/2)
  objects.left.shape = love.physics.newRectangleShape(barrierThickness, height) --make a rectangle with a width of height and a height of 50
  objects.left.fixture = love.physics.newFixture(objects.left.body, objects.left.shape) --attach shape to body


  
  --let's create a ball
  objects.ball = {}
  objects.ball.body = love.physics.newBody(world, width/2, height/2, "dynamic") --place the body in the center of the world and make it dynamic, so it can move around
  objects.ball.shape = love.physics.newCircleShape( 20) --the ball's shape has a radius of 20
  objects.ball.fixture = love.physics.newFixture(objects.ball.body, objects.ball.shape, 1) -- Attach fixture to body and give it a density of 1.
  objects.ball.fixture:setRestitution(0.3) --let the ball bounce

  --let's create a couple blocks to play around with
  objects.block1 = {}
  objects.block1.body = love.physics.newBody(world, 200, 550, "dynamic")
  objects.block1.shape = love.physics.newRectangleShape(0, 0, 50, 100)
  objects.block1.fixture = love.physics.newFixture(objects.block1.body, objects.block1.shape, 5) -- A higher density gives it more mass.

  objects.block2 = {}
  objects.block2.body = love.physics.newBody(world, 200, 400, "dynamic")
  objects.block2.shape = love.physics.newRectangleShape(0, 0, 100, 50)
  objects.block2.fixture = love.physics.newFixture(objects.block2.body, objects.block2.shape, 2)


  --initial graphics setup
  love.graphics.setBackgroundColor(0.41, 0.53, 0.97) --set the background color to a nice blue
  love.window.setMode(width, height) --set the window dimensions to 650 by 650 with no fullscreen, vsync on, and no antialiasing
end

function love.update(dt)
  world:update(dt) --this puts the world into motion

  

  speed = 200

  x_dir = bool_to_number(love.keyboard.isDown("d")) - bool_to_number(love.keyboard.isDown("a")) 
  y_dir = bool_to_number(love.keyboard.isDown("s")) - bool_to_number(love.keyboard.isDown("w")) 

    objects.ball.body:applyForce(speed * x_dir, speed * y_dir)

end

function love.mousemoved(X,Y,DX,DY)
  x,y,dx,dy = X,Y,DX,DY
  rotationAngle = rotationAngle + dx * sensitivity
end

function bool_to_number(value)
  return value and 1 or 0
end

function love.draw()
  love.graphics.setColor(0.28, 0.63, 0.05) -- set the drawing color to green for the bottom
  love.graphics.polygon("fill", objects.bottom.body:getWorldPoints(objects.bottom.shape:getPoints())) -- draw a "filled in" polygon using the bottom's coordinates
  love.graphics.polygon("fill", objects.top.body:getWorldPoints(objects.top.shape:getPoints())) -- draw a "filled in" polygon using the top's coordinates
  love.graphics.polygon("fill", objects.left.body:getWorldPoints(objects.left.shape:getPoints())) -- draw a "filled in" polygon using the left's coordinates
  love.graphics.polygon("fill", objects.right.body:getWorldPoints(objects.right.shape:getPoints())) -- draw a "filled in" polygon using the right's coordinates

  love.graphics.setColor(0.76, 0.18, 0.05) --set the drawing color to red for the ball
  love.graphics.circle("fill", objects.ball.body:getX(), objects.ball.body:getY(), objects.ball.shape:getRadius())

  love.graphics.line(objects.ball.body:getX(), objects.ball.body:getY(), objects.ball.body:getX() + math.cos(rotationAngle) * aimLength , objects.ball.body:getY()+ math.sin(rotationAngle) * aimLength)

  love.graphics.setColor(0.20, 0.20, 0.20) -- set the drawing color to grey for the blocks
  love.graphics.polygon("fill", objects.block1.body:getWorldPoints(objects.block1.shape:getPoints()))
  love.graphics.polygon("fill", objects.block2.body:getWorldPoints(objects.block2.shape:getPoints()))
end

